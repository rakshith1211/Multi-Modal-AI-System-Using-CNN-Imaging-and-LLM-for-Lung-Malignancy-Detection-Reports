# Quick Start Guide

Get your Lung Cancer Classifier up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- 8GB+ RAM recommended
- GPU optional (but recommended for training)

## Installation Steps

### 1. Run Setup Script

```bash
python setup.py
```

This will:
- Check Python version
- Create necessary directories
- Generate .env file
- Verify dataset structure
- Install dependencies (if you choose)

### 2. Configure Environment

Edit `.env` file:

```env
FLASK_SECRET_KEY=your-random-secret-key-here
OPENAI_API_KEY=sk-your-openai-key-here  # Optional
```

### 3. Fix Dataset Names (if needed)

If your training folders have extended names:

```bash
python fix_dataset_names.py
```

### 4. Train Model

```bash
python train_model.py
```

Expected output:
```
Training Configuration:
  epochs: 30
  batch_size: 16
  learning_rate: 0.001
  ...

Epoch [1/30]
  Training   - Loss: 0.8234 | Accuracy: 65.23%
  Validation - Loss: 0.7123 | Accuracy: 72.45%
  ✓ Best model saved!
```

Training time: 1-3 hours depending on hardware

### 5. Start Application

```bash
python app.py
```

Output:
```
✓ Database initialized: sqlite:///users.db
✓ Primary user already exists
✓ Model loaded successfully
 * Running on http://0.0.0.0:5000
```

### 6. Access Web Interface

Open browser to: `http://localhost:5000`

**Default Login:**
- Username: `rakshith`
- Password: `Rakshith@21`

## Quick Test

1. Login to the application
2. Navigate to "Prediction" page
3. Upload a CT scan image from `DATASET/test/`
4. View prediction results and medical report

## Common Commands

```bash
# Fix dataset folder names
python fix_dataset_names.py

# Train model
python train_model.py

# Start web application
python app.py

# Install dependencies
pip install -r requirements.txt

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

## Troubleshooting

### Issue: "Module not found"
```bash
pip install -r requirements.txt
```

### Issue: "CUDA out of memory"
Edit `train_model.py`:
```python
config = {
    'batch_size': 8,  # Reduce from 16
    ...
}
```

### Issue: "Dataset directory not found"
Ensure you have:
```
DATASET/
├── train/
├── valid/
└── test/
```

### Issue: "Model file not found"
Train the model first:
```bash
python train_model.py
```

## Next Steps

- Read full documentation: `README.md`
- Customize training: Edit `train_model.py`
- Add users: Use registration page
- Configure OpenAI: Add API key to `.env`

## Support

For detailed documentation and troubleshooting, see `README.md`
