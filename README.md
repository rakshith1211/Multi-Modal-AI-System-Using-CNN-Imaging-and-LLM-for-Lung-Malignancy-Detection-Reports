# Enhanced Clinical-Grade Lung Cancer Classifier

A production-ready deep learning application for lung cancer classification using EfficientNet-B4, Flask, and PyTorch.

## Features

- **Deep Learning Model**: EfficientNet-B4 with transfer learning
- **4-Class Classification**: Adenocarcinoma, Large Cell Carcinoma, Squamous Cell Carcinoma, Normal
- **Web Interface**: Flask-based responsive UI
- **User Authentication**: SQLite database with secure password hashing
- **Medical Reports**: GPT-powered comprehensive medical reports (with fallback)
- **Performance Metrics**: Detailed model evaluation and visualization

## Project Structure

```
lung-cancer-classifier/
├── app.py                          # Main Flask application
├── config.py                       # Centralized configuration
├── database.py                     # SQLAlchemy models
├── predictor.py                    # Prediction engine
├── model_trainer.py                # Training utilities
├── train_model.py                  # Training script
├── medical_report_generator.py     # Report generation
├── data_preprocessor.py            # Data preprocessing
├── fix_dataset_names.py            # Dataset folder renaming utility
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
├── DATASET/                        # Dataset directory
│   ├── train/                      # Training images
│   ├── valid/                      # Validation images
│   └── test/                       # Test images
├── models/                         # Trained models
│   └── best_model.pth             # Best model weights
├── uploads/                        # Temporary upload directory
└── templates/                      # HTML templates
```

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd lung-cancer-classifier
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here-change-this

# OpenAI API (Optional - for GPT-powered reports)
OPENAI_API_KEY=your-openai-api-key-here

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///users.db

# Environment
FLASK_ENV=development
```

## Dataset Setup

### Step 1: Fix Dataset Folder Names

If your training folders have extended names (e.g., `adenocarcinoma_left.lower.lobe_T2_N0_M0_Ib`), run the renaming script:

```bash
python fix_dataset_names.py
```

This will:
- Rename training/validation folders to match test folder structure
- Map extended names to base cancer types
- Verify dataset consistency

### Step 2: Verify Dataset Structure

Ensure your dataset follows this structure:

```
DATASET/
├── train/
│   ├── adenocarcinoma/
│   ├── large.cell.carcinoma/
│   ├── normal/
│   └── squamous.cell.carcinoma/
├── valid/
│   ├── adenocarcinoma/
│   ├── large.cell.carcinoma/
│   ├── normal/
│   └── squamous.cell.carcinoma/
└── test/
    ├── adenocarcinoma/
    ├── large.cell.carcinoma/
    ├── normal/
    └── squamous.cell.carcinoma/
```

## Training the Model

### Quick Start Training

```bash
python train_model.py
```

### Training Features

- **Transfer Learning**: Pre-trained EfficientNet-B4
- **Focal Loss**: Handles class imbalance
- **AdamW Optimizer**: Better generalization
- **Learning Rate Scheduling**: ReduceLROnPlateau
- **Early Stopping**: Prevents overfitting
- **Automatic Checkpointing**: Saves best model

### Training Configuration

Edit `train_model.py` to customize:

```python
config = {
    'epochs': 30,
    'batch_size': 16,
    'learning_rate': 0.001,
    'weight_decay': 0.01,
    'patience': 5,  # Early stopping
}
```

### Training Output

- Model saved to: `models/best_model.pth`
- Confusion matrix: `confusion_matrix.png`
- Training logs: `training_YYYYMMDD_HHMMSS.log`

## Running the Application

### 1. Initialize Database

The database is automatically created on first run with a default user:

- Username: `rakshith`
- Password: `Rakshith@21`

### 2. Start Flask Server

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

### 3. Access the Application

1. Open browser to `http://localhost:5000`
2. Login with credentials or register new account
3. Upload CT scan images for prediction
4. View results and medical reports

## Features Guide

### User Authentication

- **Registration**: Create new user accounts
- **Login**: Secure password-based authentication
- **Password Reset**: OTP-based password recovery
- **Session Management**: Secure session handling

### Prediction

1. Navigate to Prediction page
2. Upload CT scan image (PNG, JPG, JPEG)
3. View classification results with confidence scores
4. Download comprehensive medical report

### Performance Metrics

- Overall accuracy
- Per-class precision, recall, F1-score
- Confusion matrix visualization
- Class-wise performance breakdown

## API Endpoints

### Authentication

- `POST /register` - Register new user
- `POST /login` - User login
- `GET /logout` - User logout
- `POST /send-otp` - Send OTP for password reset
- `POST /verify-otp` - Verify OTP
- `POST /reset-password` - Reset password

### Prediction

- `POST /predict` - Upload image and get prediction
- `GET /performance` - View model performance metrics

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    mobile VARCHAR(20) UNIQUE NOT NULL,
    user_type VARCHAR(20) DEFAULT 'registered',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

### OTPs Table

```sql
CREATE TABLE otps (
    id INTEGER PRIMARY KEY,
    mobile VARCHAR(20) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    username VARCHAR(80) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);
```

## Configuration

### Centralized Settings

All configuration is managed in `config.py`:

```python
from config import get_config

# Get configuration for current environment
config = get_config('development')  # or 'production', 'testing'
```

### Environment-Specific Settings

- **Development**: Debug mode, SQL logging enabled
- **Production**: HTTPS required, optimized settings
- **Testing**: In-memory database, CSRF disabled

## Model Architecture

### EfficientNet-B4

- **Input Size**: 380x380 pixels
- **Parameters**: ~19M
- **Architecture**: Compound scaling (depth, width, resolution)
- **Transfer Learning**: ImageNet pre-trained weights
- **Custom Head**: 4-class classification layer

### Training Strategy

1. **Data Augmentation**: Random flips, rotations, color jitter
2. **Focal Loss**: α=1, γ=2 for class imbalance
3. **Optimizer**: AdamW with weight decay 0.01
4. **Learning Rate**: 0.001 with ReduceLROnPlateau
5. **Early Stopping**: Patience of 5 epochs

## Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
```bash
# Reduce batch size in train_model.py
batch_size = 8  # or 4
```

**2. OpenAI API Errors**
- Check API key in `.env`
- Verify API quota
- Application will use fallback reports automatically

**3. Database Locked**
```bash
# Delete and recreate database
rm users.db
python app.py  # Will recreate automatically
```

**4. Model Not Found**
```bash
# Train model first
python train_model.py
```

## Production Deployment

### Security Checklist

- [ ] Change `FLASK_SECRET_KEY` in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS
- [ ] Use production database (PostgreSQL recommended)
- [ ] Configure proper logging
- [ ] Set up backup strategy
- [ ] Implement rate limiting
- [ ] Add CSRF protection

### Recommended Stack

- **Web Server**: Gunicorn or uWSGI
- **Reverse Proxy**: Nginx
- **Database**: PostgreSQL
- **Caching**: Redis
- **Monitoring**: Prometheus + Grafana

## License

This project is for educational and research purposes only. Not intended for clinical use without proper validation and regulatory approval.

## Disclaimer

⚠️ **IMPORTANT**: This AI system is designed to assist healthcare professionals, not replace them. All predictions must be validated by qualified medical practitioners before any clinical decisions are made.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Acknowledgments

- EfficientNet architecture by Google Research
- PyTorch deep learning framework
- Flask web framework
- OpenAI GPT for medical report generation
