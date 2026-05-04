#!/usr/bin/env python3
"""
Enhanced Training Script for Lung Cancer Classifier
Features:
- EfficientNet-B4 with transfer learning
- AdamW optimizer with weight decay
- Focal Loss for class imbalance
- ReduceLROnPlateau scheduler
- Early stopping
- Automatic best model saving
- Comprehensive logging
"""

import os
import sys
import torch
import logging
from datetime import datetime
from model_trainer import EnhancedTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_dataset_structure(data_dir):
    """
    Verify dataset structure and count images per class
    
    Args:
        data_dir: Base dataset directory
        
    Returns:
        bool: True if structure is valid
    """
    logger.info("Verifying dataset structure...")
    
    required_dirs = ['train', 'valid', 'test']
    expected_classes = ['adenocarcinoma', 'large.cell.carcinoma', 'normal', 'squamous.cell.carcinoma']
    
    for split in required_dirs:
        split_path = os.path.join(data_dir, split)
        if not os.path.exists(split_path):
            logger.error(f"Required directory '{split_path}' not found!")
            return False
        
        # Check class folders
        class_folders = [d for d in os.listdir(split_path) 
                        if os.path.isdir(os.path.join(split_path, d))]
        
        logger.info(f"\n{split.upper()} split:")
        for class_name in class_folders:
            class_path = os.path.join(split_path, class_name)
            image_count = len([f for f in os.listdir(class_path) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            logger.info(f"  - {class_name}: {image_count} images")
    
    return True

def main():
    """Main training function"""
    logger.info("=" * 80)
    logger.info("Enhanced Lung Cancer Classifier - Model Training")
    logger.info("=" * 80)
    
    # Check CUDA availability
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Device: {device}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA Version: {torch.version.cuda}")
    
    # Dataset configuration
    data_dir = 'DATASET'
    
    if not os.path.exists(data_dir):
        logger.error(f"Dataset directory '{data_dir}' not found!")
        logger.error("Please ensure the DATASET folder is in the project root.")
        return False
    
    # Verify dataset structure
    if not verify_dataset_structure(data_dir):
        logger.error("Dataset structure verification failed!")
        return False
    
    logger.info("\n✓ Dataset structure verified successfully")
    
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Training configuration
    config = {
        'num_classes': 4,
        'model_name': 'efficientnet-b4',
        'epochs': 30,
        'batch_size': 16,
        'learning_rate': 0.001,
        'weight_decay': 0.01,
        'patience': 5,  # Early stopping patience
        'save_path': 'models/best_model.pth'
    }
    
    logger.info("\nTraining Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")
    
    try:
        # Initialize trainer
        logger.info("\nInitializing Enhanced Trainer...")
        trainer = EnhancedTrainer(
            num_classes=config['num_classes'],
            model_name=config['model_name']
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("Starting Model Training...")
        logger.info("This may take 1-3 hours depending on your hardware")
        logger.info("=" * 80 + "\n")
        
        # Train the model
        model, history = trainer.train_model(
            data_dir=data_dir,
            epochs=config['epochs'],
            batch_size=config['batch_size'],
            learning_rate=config['learning_rate'],
            weight_decay=config['weight_decay'],
            patience=config['patience'],
            save_path=config['save_path']
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("Training Completed Successfully!")
        logger.info("=" * 80)
        
        # Evaluate the model
        logger.info("\nEvaluating model on test set...")
        report, cm = trainer.evaluate_model(config['save_path'], data_dir)
        
        logger.info("\n" + "=" * 80)
        logger.info("Final Model Performance Metrics")
        logger.info("=" * 80)
        logger.info(f"\nOverall Accuracy: {report['accuracy']*100:.2f}%")
        logger.info(f"Macro Avg Precision: {report['macro avg']['precision']*100:.2f}%")
        logger.info(f"Macro Avg Recall: {report['macro avg']['recall']*100:.2f}%")
        logger.info(f"Macro Avg F1-Score: {report['macro avg']['f1-score']*100:.2f}%")
        
        logger.info("\nPer-Class Performance:")
        class_names = ['adenocarcinoma', 'large.cell.carcinoma', 'normal', 'squamous.cell.carcinoma']
        for class_name in class_names:
            if class_name in report:
                metrics = report[class_name]
                logger.info(f"\n{class_name.replace('.', ' ').title()}:")
                logger.info(f"  Precision: {metrics['precision']*100:.2f}%")
                logger.info(f"  Recall: {metrics['recall']*100:.2f}%")
                logger.info(f"  F1-Score: {metrics['f1-score']*100:.2f}%")
                logger.info(f"  Support: {metrics['support']}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Training Summary")
        logger.info("=" * 80)
        logger.info(f"✓ Best model saved to: {config['save_path']}")
        logger.info(f"✓ Confusion matrix saved to: confusion_matrix.png")
        logger.info(f"✓ Training history saved")
        logger.info("=" * 80)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n\nTraining interrupted by user!")
        logger.info("Partial progress may have been saved.")
        return False
        
    except Exception as e:
        logger.error(f"\n\nTraining failed with error: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)