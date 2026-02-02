# Virtual Environment Setup

## Create Virtual Environment

### Windows (PowerShell/CMD)
```bash
# Navigate to project directory
cd c:\Users\ASUS\Desktop\yogesh_p\dynamic_rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# PowerShell:
venv\Scripts\Activate.ps1

# CMD:
venv\Scripts\activate.bat
```

### Linux/macOS
```bash
# Navigate to project directory
cd ~/dynamic_rag

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

## Install Dependencies

After activating the virtual environment:

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Or using uv (faster)
pip install uv
uv pip install -r requirements.txt
```

## Verify Installation

```bash
# Check Python is from venv
python --version
where python  # Windows
which python  # Linux/macOS

# List installed packages
pip list
```

## Run the Application

```bash
# Make sure venv is activated (you should see (venv) in prompt)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Deactivate Virtual Environment

```bash
deactivate
```

## Quick Commands

```bash
# Full setup (Windows CMD)
python -m venv venv
venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload

# Full setup (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```
