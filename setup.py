#!/usr/bin/env python3
"""
Setup Script for Lung Cancer Classifier
Automates initial project setup and verification
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def print_step(step_num, text):
    """Print step information"""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)

def check_python_version():
    """Verify Python version"""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        return False
    
    print("✓ Python version is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    print_step(2, "Creating Project Directories")
    
    directories = [
        'models',
        'uploads',
        'logs',
        'static/images'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {directory}/")
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    print_step(3, "Setting Up Environment Variables")
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists, skipping...")
        return True
    
    env_content = """# Flask Configuration
FLASK_SECRET_KEY=change-this-to-a-random-secret-key-in-production
FLASK_ENV=development

# OpenAI API (Optional - for GPT-powered medical reports)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///users.db

# Model Configuration (Optional)
MODEL_PATH=models/best_model.pth

# Logging
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ Created .env file")
    print("⚠️  IMPORTANT: Edit .env and set your FLASK_SECRET_KEY and OPENAI_API_KEY")
    return True

def check_dataset():
    """Verify dataset structure"""
    print_step(4, "Checking Dataset Structure")
    
    if not os.path.exists('DATASET'):
        print("⚠️  DATASET directory not found")
        print("   Please create DATASET/ with train/, valid/, and test/ subdirectories")
        return False
    
    required_splits = ['train', 'valid', 'test']
    expected_classes = ['adenocarcinoma', 'large.cell.carcinoma', 'normal', 'squamous.cell.carcinoma']
    
    all_good = True
    for split in required_splits:
        split_path = os.path.join('DATASET', split)
        if not os.path.exists(split_path):
            print(f"❌ Missing: DATASET/{split}/")
            all_good = False
        else:
            classes = [d for d in os.listdir(split_path) 
                      if os.path.isdir(os.path.join(split_path, d))]
            print(f"✓ Found DATASET/{split}/ with {len(classes)} class(es)")
            
            # Check if renaming is needed
            needs_renaming = any('_' in c and c not in expected_classes for c in classes)
            if needs_renaming:
                print(f"  ⚠️  Some folders have extended names. Run: python fix_dataset_names.py")
    
    return all_good

def install_dependencies():
    """Install Python dependencies"""
    print_step(5, "Installing Dependencies")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    print("Installing packages from requirements.txt...")
    print("This may take several minutes...\n")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("\n✓ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install dependencies")
        print("   Try manually: pip install -r requirements.txt")
        return False

def verify_installation():
    """Verify key packages are installed"""
    print_step(6, "Verifying Installation")
    
    required_packages = [
        'flask',
        'torch',
        'efficientnet_pytorch',
        'flask_sqlalchemy',
        'dotenv'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            all_installed = False
    
    return all_installed

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    print("Next Steps:")
    print("\n1. Configure Environment Variables:")
    print("   - Edit .env file")
    print("   - Set FLASK_SECRET_KEY to a random secret")
    print("   - (Optional) Add OPENAI_API_KEY for GPT-powered reports")
    
    print("\n2. Prepare Dataset:")
    print("   - Ensure DATASET/ folder has train/, valid/, test/ subdirectories")
    print("   - Run: python fix_dataset_names.py (if needed)")
    
    print("\n3. Train Model:")
    print("   - Run: python train_model.py")
    print("   - This will create models/best_model.pth")
    
    print("\n4. Start Application:")
    print("   - Run: python app.py")
    print("   - Open browser to: http://localhost:5000")
    print("   - Default login: username=rakshith, password=Rakshith@21")
    
    print("\n5. (Optional) Create New User:")
    print("   - Click 'Register' on login page")
    print("   - Fill in registration form")
    
    print("\n" + "=" * 80)
    print("For detailed documentation, see README.md")
    print("=" * 80 + "\n")

def main():
    """Main setup function"""
    print_header("Lung Cancer Classifier - Setup Script")
    
    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Creating .env file", create_env_file),
        ("Checking dataset", check_dataset),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n⚠️  Warning: {step_name} encountered issues")
            print("   You may need to fix these manually")
    
    # Ask about installing dependencies
    print("\n" + "=" * 80)
    response = input("Install Python dependencies now? (y/n): ").lower().strip()
    
    if response == 'y':
        install_dependencies()
        verify_installation()
    else:
        print("\nSkipping dependency installation.")
        print("Install later with: pip install -r requirements.txt")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nSetup failed with error: {str(e)}")
        sys.exit(1)
