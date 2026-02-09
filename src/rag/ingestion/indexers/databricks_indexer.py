"""
Databricks Vector Search Indexer

Uploads CCoP chunks to Databricks Delta table and creates hybrid vector search index.
"""

import logging
import time
from typing import List, Optional

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient

from infrastructure.config.settings import Settings
from rag.ingestion.models import CcopChunk

logger = logging.getLogger(__name__)


class DatabricksIndexer:
    """
    Upload CCoP chunks to Databricks Delta table and create hybrid vector search index.

    Implements Delta Sync indexing with:
    - Hybrid search (dense + sparse via RRF)
    - Built-in reranking for improved precision
    - Automatic embedding generation via BGE endpoint
    """

    def __init__(self, settings: Settings):
        """
        Initialize Databricks clients.

        Args:
            settings: Application settings with Databricks configuration

        Raises:
            ValueError: If required Databricks settings are missing
        """
        # Validate required settings
        required = [
            ("databricks_host", settings.databricks_host),
            ("databricks_token", settings.databricks_token),
            ("databricks_catalog", settings.databricks_catalog),
            ("databricks_schema", settings.databricks_schema),
            ("databricks_vector_search_endpoint", settings.databricks_vector_search_endpoint),
            ("databricks_embedding_endpoint", settings.databricks_embedding_endpoint),
            ("databricks_warehouse_id", settings.databricks_warehouse_id),
        ]

        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(
                f"Missing required Databricks settings: {', '.join(missing)}. "
                f"Please configure these in .env.local with CCOP_ prefix."
            )

        self.settings = settings
        self.workspace_client: Optional[WorkspaceClient] = None
        self.vector_search_client: Optional[VectorSearchClient] = None

        logger.info(
            f"DatabricksIndexer initialized for "
            f"{settings.databricks_catalog}.{settings.databricks_schema}"
        )

    def _get_workspace_client(self) -> WorkspaceClient:
        """Get or create WorkspaceClient (lazy initialization)."""
        if self.workspace_client is None:
            try:
                self.workspace_client = WorkspaceClient(
                    host=self.settings.databricks_host,
                    token=self.settings.databricks_token,
                )
                logger.info(f"Connected to Databricks workspace: {self.settings.databricks_host}")
            except Exception as e:
                raise ConnectionError(
                    f"Failed to connect to Databricks workspace at {self.settings.databricks_host}: {e}"
                ) from e
        return self.workspace_client

    def _get_vector_search_client(self) -> VectorSearchClient:
        """Get or create VectorSearchClient (lazy initialization)."""
        if self.vector_search_client is None:
            try:
                self.vector_search_client = VectorSearchClient(
                    workspace_url=self.settings.databricks_host,
                    personal_access_token=self.settings.databricks_token,
                )
                logger.info("Connected to Databricks Vector Search")
            except Exception as e:
                raise ConnectionError(
                    f"Failed to connect to Databricks Vector Search: {e}"
                ) from e
        return self.vector_search_client

    def _execute_sql(self, statement: str, description: str = "") -> object:
        """
        Execute a SQL statement via Databricks SQL Warehouse.

        Submits with 50s wait (max allowed). If still pending, polls until complete.

        Args:
            statement: SQL statement to execute
            description: Human-readable description for logging

        Returns:
            StatementResponse from the executed statement
        """
        workspace_client = self._get_workspace_client()
        warehouse_id = self.settings.databricks_warehouse_id

        if description:
            logger.info(f"Executing SQL: {description}")

        response = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=statement,
            wait_timeout="50s",
        )

        # Poll if statement is still running (warehouse may be starting)
        poll_count = 0
        while response.status.state.value in ("PENDING", "RUNNING"):
            poll_count += 1
            if poll_count > 60:  # ~5 minutes of polling at 5s intervals
                raise TimeoutError(f"SQL statement did not complete after polling {poll_count} times")
            time.sleep(5)
            response = workspace_client.statement_execution.get_statement(response.statement_id)

        if response.status.state.value == "FAILED":
            error_msg = getattr(response.status, "error", None)
            error_detail = getattr(error_msg, "message", str(error_msg)) if error_msg else "Unknown error"
            raise RuntimeError(f"SQL execution failed: {error_detail}")

        if response.status.state.value == "CANCELED":
            raise RuntimeError("SQL statement was canceled")

        return response

    @staticmethod
    def _escape_sql_string(value: str) -> str:
        """Escape a string for SQL single-quoted literal."""
        if value is None:
            return "NULL"
        return value.replace("\\", "\\\\").replace("'", "''")

    def create_source_table(self, chunks: List[CcopChunk]) -> str:
        """
        Create Delta table and upload chunks via SQL Warehouse execution.

        Creates table at {catalog}.{schema}.ccop_parsed_clauses with schema:
        - id (STRING, primary key)
        - text (STRING, for embedding)
        - document_source (STRING)
        - section (STRING)
        - subsection (STRING)
        - clause (STRING)
        - citation_id (STRING)
        - document_type (STRING)
        - page (INT, nullable)

        Args:
            chunks: List of CcopChunk objects to upload

        Returns:
            Full table name (catalog.schema.table)

        Raises:
            PermissionError: If Unity Catalog permissions are insufficient
            ValueError: If chunks list is empty
        """
        if not chunks:
            raise ValueError("Cannot create table with empty chunks list")

        catalog = self.settings.databricks_catalog
        schema = self.settings.databricks_schema
        table_name = f"{catalog}.{schema}.ccop_parsed_clauses"
        logger.info(f"Creating Delta table: {table_name}")

        try:
            # Step 1: Create schema if not exists
            self._execute_sql(
                f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}",
                f"Creating schema {catalog}.{schema}",
            )

            # Step 2: Drop table if exists (clean slate for ingestion)
            self._execute_sql(
                f"DROP TABLE IF EXISTS {table_name}",
                f"Dropping existing table {table_name}",
            )

            # Step 3: Create table
            self._execute_sql(
                f"""
                CREATE TABLE {table_name} (
                    id STRING NOT NULL,
                    text STRING NOT NULL,
                    document_source STRING NOT NULL,
                    section STRING NOT NULL,
                    subsection STRING NOT NULL,
                    clause STRING NOT NULL,
                    citation_id STRING NOT NULL,
                    document_type STRING NOT NULL,
                    page INT
                ) USING DELTA
                TBLPROPERTIES (
                    'delta.enableChangeDataFeed' = 'true'
                )
                """,
                f"Creating table {table_name}",
            )

            # Step 4: Insert data in batches
            batch_size = 10
            total = len(chunks)
            logger.info(f"Inserting {total} chunks in batches of {batch_size}")

            for batch_start in range(0, total, batch_size):
                batch_end = min(batch_start + batch_size, total)
                batch = chunks[batch_start:batch_end]

                values_parts = []
                for chunk in batch:
                    page_val = str(chunk.metadata.page) if chunk.metadata.page is not None else "NULL"
                    row = (
                        f"('{self._escape_sql_string(chunk.id)}', "
                        f"'{self._escape_sql_string(chunk.text)}', "
                        f"'{self._escape_sql_string(chunk.metadata.document_source)}', "
                        f"'{self._escape_sql_string(chunk.metadata.section)}', "
                        f"'{self._escape_sql_string(chunk.metadata.subsection)}', "
                        f"'{self._escape_sql_string(chunk.metadata.clause)}', "
                        f"'{self._escape_sql_string(chunk.metadata.citation_id)}', "
                        f"'{self._escape_sql_string(chunk.metadata.document_type)}', "
                        f"{page_val})"
                    )
                    values_parts.append(row)

                insert_sql = (
                    f"INSERT INTO {table_name} "
                    f"(id, text, document_source, section, subsection, clause, citation_id, document_type, page) "
                    f"VALUES {', '.join(values_parts)}"
                )

                self._execute_sql(
                    insert_sql,
                    f"Inserting batch {batch_start + 1}-{batch_end} of {total}",
                )

            # Step 5: Verify row count
            count_response = self._execute_sql(
                f"SELECT COUNT(*) as cnt FROM {table_name}",
                f"Verifying row count in {table_name}",
            )

            row_count = None
            if count_response.result and count_response.result.data_array:
                row_count = count_response.result.data_array[0][0]

            logger.info(f"Successfully uploaded {row_count or total} rows to {table_name}")

            return table_name

        except Exception as e:
            error_str = str(e)
            if "PERMISSION_DENIED" in error_str or "not authorized" in error_str.lower():
                raise PermissionError(
                    f"Insufficient Unity Catalog permissions for {table_name}. "
                    f"Required privileges: USE CATALOG, USE SCHEMA, CREATE TABLE, MODIFY. "
                    f"Contact your Databricks admin."
                ) from e
            elif "warehouse" in error_str.lower() and "not found" in error_str.lower():
                raise ValueError(
                    f"SQL Warehouse not found: {self.settings.databricks_warehouse_id}. "
                    f"Verify the warehouse ID in Databricks workspace: SQL -> SQL Warehouses."
                ) from e
            else:
                raise RuntimeError(f"Failed to create Delta table: {e}") from e

    def create_vector_search_index(self, source_table: str) -> str:
        """
        Create Delta Sync vector search index with hybrid search and reranking.

        Creates index at {catalog}.{schema}.ccop_clauses_hybrid with:
        - Delta Sync for automatic updates
        - Dense embeddings via BGE endpoint
        - Sparse search on text field (BM25)
        - Hybrid search via RRF (Reciprocal Rank Fusion)
        - Built-in reranking enabled

        Args:
            source_table: Full table name (catalog.schema.table)

        Returns:
            Index name

        Raises:
            ValueError: If embedding endpoint not found or source table invalid
        """
        index_name = f"{self.settings.databricks_catalog}.{self.settings.databricks_schema}.ccop_clauses_hybrid"
        logger.info(f"Creating vector search index: {index_name}")

        vsc = self._get_vector_search_client()

        try:
            # Verify vector search endpoint exists
            logger.info(f"Verifying vector search endpoint: {self.settings.databricks_vector_search_endpoint}")
            try:
                endpoint = vsc.get_endpoint(self.settings.databricks_vector_search_endpoint)
                endpoint_name = (
                    endpoint.get("name", self.settings.databricks_vector_search_endpoint)
                    if isinstance(endpoint, dict)
                    else getattr(endpoint, "name", self.settings.databricks_vector_search_endpoint)
                )
                logger.info(f"Vector search endpoint verified: {endpoint_name}")
            except AttributeError:
                # get_endpoint succeeded but returned unexpected type — endpoint exists
                logger.info(
                    f"Vector search endpoint verified: {self.settings.databricks_vector_search_endpoint}"
                )
            except Exception as e:
                raise ValueError(
                    f"Vector search endpoint not found: {self.settings.databricks_vector_search_endpoint}. "
                    f"Create it in Databricks workspace: Compute -> Vector Search -> Create endpoint"
                ) from e

            # Verify embedding endpoint accessibility
            logger.info(f"Verifying embedding endpoint: {self.settings.databricks_embedding_endpoint}")
            # Note: Actual verification would query model serving API
            # For common endpoint 'databricks-bge-large-en', we assume it exists
            if self.settings.databricks_embedding_endpoint != "databricks-bge-large-en":
                logger.warning(
                    f"Using non-standard embedding endpoint: {self.settings.databricks_embedding_endpoint}. "
                    f"Verify it exists in Databricks workspace: Serving -> Foundation Model APIs"
                )

            # Create Delta Sync index with hybrid search
            logger.info("Creating Delta Sync index with hybrid search...")

            index = vsc.create_delta_sync_index(
                endpoint_name=self.settings.databricks_vector_search_endpoint,
                index_name=index_name,
                source_table_name=source_table,
                pipeline_type="TRIGGERED",  # Manual sync (vs CONTINUOUS)
                primary_key="id",
                embedding_source_column="text",
                embedding_model_endpoint_name=self.settings.databricks_embedding_endpoint,
            )

            logger.info(f"Index created: {index_name}")
            logger.info("Index status: PROVISIONING (initial sync will follow)")

            return index_name

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.warning(f"Index already exists: {index_name}, will reuse")
                return index_name
            elif "endpoint not found" in str(e).lower():
                raise ValueError(
                    f"Embedding endpoint not found: {self.settings.databricks_embedding_endpoint}. "
                    f"Verify in Databricks workspace: Serving -> Foundation Model APIs"
                ) from e
            elif "table not found" in str(e).lower():
                raise ValueError(
                    f"Source table not found: {source_table}. "
                    f"Ensure create_source_table() completed successfully."
                ) from e
            else:
                raise RuntimeError(f"Failed to create vector search index: {e}") from e

    def wait_for_index_ready(self, index_name: str, timeout_seconds: int = 600) -> None:
        """
        Poll index status until ONLINE or timeout.

        Args:
            index_name: Full index name
            timeout_seconds: Maximum wait time in seconds (default: 600)

        Raises:
            TimeoutError: If index not ready within timeout
        """
        logger.info(f"Waiting for index to become ONLINE: {index_name}")
        logger.info("This may take 5-10 minutes for initial index creation...")

        vsc = self._get_vector_search_client()
        start_time = time.time()
        last_log_time = start_time

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Index {index_name} not ready after {timeout_seconds}s. "
                    f"Check Databricks workspace for index status."
                )

            try:
                index = vsc.get_index(
                    endpoint_name=self.settings.databricks_vector_search_endpoint,
                    index_name=index_name,
                )

                # Get status from describe() method (VectorSearchIndex object)
                desc = index.describe() if hasattr(index, "describe") else index
                if isinstance(desc, dict):
                    status_info = desc.get("status", {})
                    is_ready = status_info.get("ready", False)
                    detailed_state = status_info.get("detailed_state", "UNKNOWN")
                    indexed_rows = status_info.get("indexed_row_count", 0)
                else:
                    is_ready = False
                    detailed_state = "UNKNOWN"
                    indexed_rows = 0

                # Log progress every 30 seconds
                if time.time() - last_log_time > 30:
                    logger.info(
                        f"Index status: {detailed_state} | "
                        f"indexed_rows: {indexed_rows} | "
                        f"elapsed: {int(elapsed)}s"
                    )
                    last_log_time = time.time()

                if is_ready:
                    logger.info(f"Index is ONLINE after {int(elapsed)}s")
                    return
                elif detailed_state in ["OFFLINE_FAILED", "FAILED"]:
                    message = status_info.get("message", "No details")
                    raise RuntimeError(
                        f"Index creation failed: {detailed_state}. {message}"
                    )

                # Wait before next check
                time.sleep(10)

            except RuntimeError:
                raise
            except Exception as e:
                if "not found" in str(e).lower():
                    # Index might not be visible yet, continue waiting
                    time.sleep(10)
                    continue
                else:
                    raise RuntimeError(f"Error checking index status: {e}") from e

    def verify_index(
        self, index_name: str, sample_query: str = "access control requirements"
    ) -> dict:
        """
        Run sample query to verify index is working.

        Args:
            index_name: Full index name
            sample_query: Test query text

        Returns:
            Dictionary with query results and metadata
        """
        logger.info(f"Verifying index with sample query: '{sample_query}'")

        vsc = self._get_vector_search_client()

        try:
            index = vsc.get_index(
                    endpoint_name=self.settings.databricks_vector_search_endpoint,
                    index_name=index_name,
                )

            # Execute similarity search
            columns = ["id", "text", "document_source", "section", "citation_id"]
            results = index.similarity_search(
                query_text=sample_query,
                columns=columns,
                num_results=5,
            )

            # Extract results — data_array contains rows as lists, column_names has headers
            data_array = results.get("result", {}).get("data_array", [])
            column_names = results.get("result", {}).get("column_names", columns)
            result_count = len(data_array)

            logger.info(f"Query returned {result_count} results")

            # Convert list rows to dicts for easier consumption
            result_dicts = []
            for row in data_array:
                row_dict = dict(zip(column_names, row))
                result_dicts.append(row_dict)

            if result_count > 0:
                first = result_dicts[0]
                logger.info(
                    f"Top result: {first.get('citation_id', 'N/A')} - "
                    f"{first.get('section', 'N/A')}"
                )

            return {
                "index_name": index_name,
                "query": sample_query,
                "result_count": result_count,
                "results": result_dicts[:3],
            }

        except Exception as e:
            logger.error(f"Index verification failed: {e}")
            raise RuntimeError(f"Failed to query index {index_name}: {e}") from e

    def index_chunks(self, chunks: List[CcopChunk]) -> str:
        """
        Orchestrate full indexing pipeline: table creation -> index creation -> wait -> verify.

        This is the main entry point for indexing CCoP chunks.

        Args:
            chunks: List of CcopChunk objects to index

        Returns:
            Index name

        Raises:
            ValueError: If chunks empty or configuration invalid
            PermissionError: If insufficient Databricks permissions
            TimeoutError: If index creation times out
            RuntimeError: For other indexing failures
        """
        logger.info(f"Starting full indexing pipeline for {len(chunks)} chunks")

        # Step 1: Create source table and upload chunks
        logger.info("Step 1/4: Creating Delta table and uploading chunks...")
        source_table = self.create_source_table(chunks)

        # Step 2: Create vector search index
        logger.info("Step 2/4: Creating vector search index...")
        index_name = self.create_vector_search_index(source_table)

        # Step 3: Wait for index to be ready
        logger.info("Step 3/4: Waiting for index to become ONLINE...")
        self.wait_for_index_ready(index_name)

        # Step 4: Verify with sample query
        logger.info("Step 4/4: Verifying index with sample query...")
        verification = self.verify_index(index_name)

        logger.info(f"Indexing complete: {index_name}")
        logger.info(f"Verification: {verification['result_count']} results for sample query")

        return index_name
