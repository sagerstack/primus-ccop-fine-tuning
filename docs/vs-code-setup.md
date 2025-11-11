# VS Code Setup for Llama-Primus CCoP Project

## 🔧 Option 1: Using Jupyter Notebook (Recommended)

### Install Required Extensions:
1. **Open VS Code**
2. **Go to Extensions** (Ctrl+Shift+X or Cmd+Shift+X)
3. **Install these extensions:**
   - `Jupyter` (by Microsoft)
   - `Python` (by Microsoft)
   - `Pylance` (by Microsoft, optional)

### After Installing Extensions:
1. **Open the notebook file**: `notebooks/colab/01-llama-primus-setup.ipynb`
2. **Select Python interpreter**: VS Code will prompt you to select a Python interpreter
3. **Run cells**: Use Shift+Enter or the "Run" button to execute cells

### Requirements for Local Jupyter:
```bash
# Install required packages
pip install jupyter
pip install torch torchvision torchaudio  # Choose appropriate version
pip install transformers accelerate bitsandbytes
pip install pandas matplotlib seaborn tqdm
```

## 🐍 Option 2: Using Python Script (Easier)

I've created a Python script version: `notebooks/colab/01-llama-primus-setup.py`

### Quick Start:
```bash
# 1. Navigate to project directory
cd /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc

# 2. Create virtual environment (recommended)
python -m venv primus-env
source primus-env/bin/activate  # On Windows: primus-env\Scripts\activate

# 3. Install dependencies
pip install torch torchvision torchaudio  # For CPU: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers accelerate bitsandbytes
pip install pandas matplotlib seaborn tqdm datasets

# 4. Run the script
python notebooks/colab/01-llama-primus-setup.py
```

## 📋 What Each Option Does:

### Jupyter Notebook (.ipynb):
- ✅ Interactive cell-by-cell execution
- ✅ Visual outputs and charts
- ✅ Easy to modify and experiment
- ✅ Rich markdown documentation
- ❌ Requires Jupyter setup

### Python Script (.py):
- ✅ Simple to run from command line
- ✅ No extra setup needed
- ✅ Same functionality as notebook
- ✅ Easier for automation
- ❌ Less interactive experience

## 🎯 Recommended Workflow:

### For Development/Testing:
```bash
# Use the Python script for quick testing
python notebooks/colab/01-llama-primus-setup.py
```

### For Detailed Analysis:
```bash
# Use Jupyter for interactive exploration
# Open: notebooks/colab/01-llama-primus-setup.ipynb in VS Code
```

## 💻 Hardware Requirements:

### **Minimum (CPU-only):**
- **RAM**: 16GB+ (will be slow)
- **Storage**: 20GB free space
- **Performance**: 30-120 seconds per response

### **Recommended (with GPU):**
- **GPU**: NVIDIA RTX 3060 (12GB) or better
- **VRAM**: 12GB+ GPU memory
- **RAM**: 32GB+ system memory
- **Performance**: 2-10 seconds per response

### **For Llama-Primus 8B Model:**
- **Model Size**: ~15GB
- **Memory Needed**: 16GB+ (GPU) or 32GB+ (CPU)
- **Recommendation**: Use Google Colab for better performance

## 🚀 Quick Test Commands:

### Test GPU Availability:
```python
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

### Test Model Loading:
```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("trendmicro-ailab/Llama-Primus-Reasoning")
print("✅ Model access successful!")
```

## 🆘 Troubleshooting:

### **Common Issues:**

1. **Out of Memory Errors:**
   ```bash
   # Use 8-bit quantization
   pip install bitsandbytes
   # The script will automatically use quantization if needed
   ```

2. **Network Issues:**
   ```bash
   # Check internet connection
   ping huggingface.co
   # Or use a different network
   ```

3. **Permission Errors:**
   ```bash
   # Use virtual environment
   python -m venv primus-env
   source primus-env/bin/activate
   ```

4. **VS Code Extension Issues:**
   - Restart VS Code
   - Clear Jupyter cache: Command Palette → "Jupyter: Clear Cache"
   - Update extensions

## 🎓 Student Tips:

### **Best Performance Strategy:**
1. **Start with Google Colab** (free T4 GPU)
2. **Use local Python script** for testing code
3. **Move to AWS** when ready for serious training

### **Cost-Effective Approach:**
- **Phase 1**: Google Colab (FREE with student benefits)
- **Phase 2**: Local testing + AWS spot instances
- **Total Cost**: $0-50 for initial development

### **Time Management:**
- **Colab Sessions**: 12-hour limit
- **Local Testing**: No time limits
- **Hybrid Approach**: Use both strategically

## 📞 Need Help?

1. **Check the script output** for specific error messages
2. **Verify GPU setup** with `nvidia-smi` (if you have NVIDIA GPU)
3. **Test internet connection** for model downloads
4. **Start with CPU version** if GPU issues persist

The Python script includes comprehensive error handling and will guide you through any setup issues!