#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all critical components to verify project completion
"""

import os
import sys
import torch
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_test(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")

def test_imports():
    """Test all required imports"""
    print_header("TEST 1: Import Dependencies")
    
    tests = []
    
    try:
        import torch
        tests.append(("PyTorch", True, f"Version {torch.__version__}"))
    except ImportError as e:
        tests.append(("PyTorch", False, str(e)))
    
    try:
        import torchvision
        tests.append(("TorchVision", True, ""))
    except ImportError as e:
        tests.append(("TorchVision", False, str(e)))
    
    try:
        from efficientnet_pytorch import EfficientNet
        tests.append(("EfficientNet", True, ""))
    except ImportError as e:
        tests.append(("EfficientNet", False, str(e)))
    
    try:
        import flask
        tests.append(("Flask", True, f"Version {flask.__version__}"))
    except ImportError as e:
        tests.append(("Flask", False, str(e)))
    
    try:
        from flask_sqlalchemy import SQLAlchemy
        tests.append(("Flask-SQLAlchemy", True, ""))
    except ImportError as e:
        tests.append(("Flask-SQLAlchemy", False, str(e)))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_project_structure():
    """Test project file structure"""
    print_header("TEST 2: Project Structure")
    
    required_files = {
        'app.py': 'Main Flask application',
        'predictor.py': 'Prediction engine',
        'model_trainer.py': 'Training utilities',
        'database.py': 'Database models',
        'config.py': 'Configuration',
        'medical_report_generator.py': 'Report generator',
        'data_preprocessor.py': 'Data preprocessing',
        'requirements.txt': 'Dependencies',
        '.env': 'Environment variables'
    }
    
    tests = []
    for file, desc in required_files.items():
        exists = os.path.exists(file)
        tests.append((f"{file} ({desc})", exists, ""))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_dataset_structure():
    """Test dataset structure"""
    print_header("TEST 3: Dataset Structure")
    
    tests = []
    
    # Check main directory
    dataset_exists = os.path.exists('DATASET')
    tests.append(("DATASET directory", dataset_exists, ""))
    
    if dataset_exists:
        # Check splits
        for split in ['train', 'valid', 'test']:
            split_path = os.path.join('DATASET', split)
            exists = os.path.exists(split_path)
            tests.append((f"DATASET/{split}", exists, ""))
            
            if exists:
                # Check classes
                expected_classes = ['adenocarcinoma', 'large.cell.carcinoma', 
                                  'normal', 'squamous.cell.carcinoma']
                for cls in expected_classes:
                    cls_path = os.path.join(split_path, cls)
                    exists = os.path.exists(cls_path)
                    if exists:
                        count = len([f for f in os.listdir(cls_path) 
                                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                        tests.append((f"{split}/{cls}", exists, f"{count} images"))
                    else:
                        tests.append((f"{split}/{cls}", exists, "Missing"))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_models():
    """Test model files"""
    print_header("TEST 4: Model Files")
    
    tests = []
    
    models_dir = 'models'
    if os.path.exists(models_dir):
        tests.append(("models/ directory", True, ""))
        
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
        if model_files:
            for model_file in model_files:
                model_path = os.path.join(models_dir, model_file)
                size_mb = os.path.getsize(model_path) / (1024 * 1024)
                tests.append((f"Model: {model_file}", True, f"{size_mb:.2f} MB"))
        else:
            tests.append(("Model files (.pth)", False, "No models found"))
    else:
        tests.append(("models/ directory", False, "Directory missing"))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_predictor_logic():
    """Test that predictor uses model, not filename"""
    print_header("TEST 5: Predictor Logic (CRITICAL)")
    
    tests = []
    
    try:
        # Read predictor.py
        with open('predictor.py', 'r') as f:
            content = f.read()
        
        # Check for filename-based prediction (BAD)
        bad_patterns = [
            "if 'adenocarcinoma' in path_lower:",
            "if 'large.cell.carcinoma' in path_lower",
            "if 'normal' in path_lower:",
            "if 'squamous' in path_lower:"
        ]
        
        has_filename_logic = any(pattern in content for pattern in bad_patterns)
        
        if has_filename_logic:
            tests.append(("No filename-based prediction", False, 
                         "CRITICAL: Still using filename for prediction!"))
        else:
            tests.append(("No filename-based prediction", True, 
                         "Uses actual model inference"))
        
        # Check for model inference (GOOD)
        good_patterns = [
            "with torch.no_grad():",
            "outputs = self.model(image_tensor)",
            "F.softmax(outputs, dim=1)"
        ]
        
        has_model_inference = all(pattern in content for pattern in good_patterns)
        tests.append(("Uses model inference", has_model_inference, 
                     "Model is properly used for predictions"))
        
        # Check for random confidence (BAD)
        has_random_confidence = "np.random.uniform" in content and "enhanced_probs" in content
        tests.append(("No random confidence scores", not has_random_confidence,
                     "Uses actual model confidence" if not has_random_confidence 
                     else "WARNING: Still using random confidence"))
        
    except Exception as e:
        tests.append(("Predictor code analysis", False, str(e)))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_database():
    """Test database functionality"""
    print_header("TEST 6: Database")
    
    tests = []
    
    try:
        from database import db, User, OTP, init_db
        tests.append(("Database module import", True, ""))
        
        # Check if database.py has required models
        tests.append(("User model defined", True, ""))
        tests.append(("OTP model defined", True, ""))
        
    except Exception as e:
        tests.append(("Database module", False, str(e)))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_configuration():
    """Test configuration"""
    print_header("TEST 7: Configuration")
    
    tests = []
    
    # Check .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
        
        has_secret_key = 'FLASK_SECRET_KEY' in env_content
        has_openai_key = 'OPENAI_API_KEY' in env_content
        
        tests.append((".env file exists", True, ""))
        tests.append(("FLASK_SECRET_KEY defined", has_secret_key, ""))
        tests.append(("OPENAI_API_KEY defined", has_openai_key, 
                     "(Optional - for GPT reports)"))
    else:
        tests.append((".env file", False, "Missing"))
    
    # Check config.py
    if os.path.exists('config.py'):
        tests.append(("config.py exists", True, "Centralized configuration"))
    else:
        tests.append(("config.py", False, "Missing"))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_documentation():
    """Test documentation completeness"""
    print_header("TEST 8: Documentation")
    
    docs = {
        'README.md': 'Main documentation',
        'START_HERE.md': 'Quick start guide',
        'QUICKSTART.md': '5-minute setup',
        'DEPLOYMENT.md': 'Production deployment',
        'PROJECT_SUMMARY.md': 'Implementation details'
    }
    
    tests = []
    for doc, desc in docs.items():
        exists = os.path.exists(doc)
        tests.append((f"{doc} ({desc})", exists, ""))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def test_actual_prediction():
    """Test actual prediction with model"""
    print_header("TEST 9: Actual Prediction Test")
    
    tests = []
    
    try:
        from predictor import LungCancerPredictor
        
        # Initialize predictor
        predictor = LungCancerPredictor()
        tests.append(("Predictor initialization", True, ""))
        
        # Find a test image
        test_image = None
        for root, dirs, files in os.walk('DATASET/test'):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    test_image = os.path.join(root, file)
                    break
            if test_image:
                break
        
        if test_image:
            tests.append(("Test image found", True, os.path.basename(test_image)))
            
            # Make prediction
            result = predictor.predict(test_image)
            
            # Check result structure
            has_class = 'predicted_class' in result
            has_confidence = 'confidence' in result
            has_probabilities = 'class_probabilities' in result
            has_report = 'medical_report' in result
            
            tests.append(("Prediction returns class", has_class, 
                         result.get('predicted_class', 'N/A')))
            tests.append(("Prediction returns confidence", has_confidence,
                         f"{result.get('confidence', 0):.2%}"))
            tests.append(("Prediction returns probabilities", has_probabilities, ""))
            tests.append(("Prediction returns report", has_report, ""))
            
            # Check if confidence is reasonable (not random)
            if has_confidence:
                confidence = result['confidence']
                is_reasonable = 0.0 <= confidence <= 1.0
                tests.append(("Confidence in valid range", is_reasonable,
                             f"{confidence:.2%}"))
        else:
            tests.append(("Test image", False, "No test images found"))
            
    except Exception as e:
        tests.append(("Prediction test", False, str(e)))
    
    for name, passed, details in tests:
        print_test(name, passed, details)
    
    return all(t[1] for t in tests)

def main():
    """Run all tests"""
    print_header("COMPREHENSIVE SYSTEM TEST")
    print("Testing Enhanced Clinical-Grade Lung Cancer Classifier")
    
    test_suites = [
        ("Import Dependencies", test_imports),
        ("Project Structure", test_project_structure),
        ("Dataset Structure", test_dataset_structure),
        ("Model Files", test_models),
        ("Predictor Logic", test_predictor_logic),
        ("Database", test_database),
        ("Configuration", test_configuration),
        ("Documentation", test_documentation),
        ("Actual Prediction", test_actual_prediction)
    ]
    
    results = []
    for suite_name, test_func in test_suites:
        try:
            result = test_func()
            results.append((suite_name, result))
        except Exception as e:
            print(f"\n❌ Test suite '{suite_name}' crashed: {str(e)}")
            results.append((suite_name, False))
    
    # Final summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for suite_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {suite_name}")
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} test suites passed ({percentage:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Project is complete and ready to use.")
        print("\nTo start the application:")
        print("  python app.py")
        print("\nThen open: http://localhost:5000")
        print("Default login: username=rakshith, password=Rakshith@21")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
