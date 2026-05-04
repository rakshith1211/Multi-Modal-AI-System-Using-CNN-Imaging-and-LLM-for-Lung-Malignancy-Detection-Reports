import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets
from efficientnet_pytorch import EfficientNet
import os
from data_preprocessor import DatasetExpander
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = nn.CrossEntropyLoss(reduction='none')(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1-pt)**self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

class EnhancedTrainer:
    def __init__(self, num_classes=4, model_name='efficientnet-b4'):
        self.num_classes = num_classes
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.class_names = ['adenocarcinoma', 'large.cell.carcinoma', 'normal', 'squamous.cell.carcinoma']
        
    def create_model(self):
        """Create EfficientNet-B4 model"""
        model = EfficientNet.from_pretrained('efficientnet-b4')
        model._fc = nn.Linear(model._fc.in_features, self.num_classes)
        return model.to(self.device)
    
    def prepare_data(self, data_dir, batch_size=16):
        """
        Prepare training and validation datasets
        
        Args:
            data_dir: Base dataset directory
            batch_size: Batch size for data loaders
            
        Returns:
            train_loader: Training data loader
            val_loader: Validation data loader
        """
        expander = DatasetExpander()
        
        train_dataset = datasets.ImageFolder(
            os.path.join(data_dir, 'train'),
            transform=expander.get_training_transforms()
        )
        
        val_dataset = datasets.ImageFolder(
            os.path.join(data_dir, 'valid'),
            transform=expander.get_validation_transforms()
        )
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        
        return train_loader, val_loader
    
    def train_model(self, data_dir, epochs=20, batch_size=16, learning_rate=0.001, 
                    weight_decay=0.01, patience=5, save_path='models/best_model.pth'):
        """
        Train the EfficientNet-B4 model with early stopping
        
        Args:
            data_dir: Base dataset directory
            epochs: Maximum number of epochs
            batch_size: Batch size for training
            learning_rate: Initial learning rate
            weight_decay: Weight decay for AdamW optimizer
            patience: Early stopping patience (epochs without improvement)
            save_path: Path to save best model
            
        Returns:
            model: Trained model
            history: Training history dictionary
        """
        print(f"\n{'='*80}")
        print("Initializing Training Process")
        print(f"{'='*80}")
        
        model = self.create_model()
        train_loader, val_loader = self.prepare_data(data_dir, batch_size)
        
        # Loss function: Focal Loss for handling class imbalance
        criterion = FocalLoss(alpha=1, gamma=2)
        
        # Optimizer: AdamW with weight decay for better generalization
        optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        
        # Scheduler: Reduce learning rate when validation loss plateaus
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', patience=3, factor=0.5, verbose=True
        )
        
        # Early stopping variables
        best_val_acc = 0.0
        best_val_loss = float('inf')
        epochs_without_improvement = 0
        
        # Training history
        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'learning_rates': []
        }
        
        print(f"\nTraining Configuration:")
        print(f"  Epochs: {epochs}")
        print(f"  Batch Size: {batch_size}")
        print(f"  Learning Rate: {learning_rate}")
        print(f"  Weight Decay: {weight_decay}")
        print(f"  Early Stopping Patience: {patience}")
        print(f"  Device: {self.device}")
        print(f"{'='*80}\n")
        
        for epoch in range(epochs):
            print(f"\nEpoch [{epoch+1}/{epochs}]")
            print("-" * 80)
            
            # Training phase
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.device), target.to(self.device)
                
                optimizer.zero_grad()
                output = model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                train_total += target.size(0)
                train_correct += (predicted == target).sum().item()
                
                # Print progress every 10 batches
                if (batch_idx + 1) % 10 == 0:
                    print(f"  Batch [{batch_idx+1}/{len(train_loader)}] - "
                          f"Loss: {loss.item():.4f}")
            
            # Validation phase
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for data, target in val_loader:
                    data, target = data.to(self.device), target.to(self.device)
                    output = model(data)
                    loss = criterion(output, target)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(output.data, 1)
                    val_total += target.size(0)
                    val_correct += (predicted == target).sum().item()
            
            # Calculate metrics
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            train_acc = 100. * train_correct / train_total
            val_acc = 100. * val_correct / val_total
            current_lr = optimizer.param_groups[0]['lr']
            
            # Store history
            history['train_loss'].append(avg_train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(avg_val_loss)
            history['val_acc'].append(val_acc)
            history['learning_rates'].append(current_lr)
            
            # Update learning rate scheduler
            scheduler.step(avg_val_loss)
            
            # Print epoch summary
            print(f"\n  Training   - Loss: {avg_train_loss:.4f} | Accuracy: {train_acc:.2f}%")
            print(f"  Validation - Loss: {avg_val_loss:.4f} | Accuracy: {val_acc:.2f}%")
            print(f"  Learning Rate: {current_lr:.6f}")
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_val_loss = avg_val_loss
                epochs_without_improvement = 0
                
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                    'val_loss': avg_val_loss,
                    'history': history
                }, save_path)
                
                print(f"  ✓ Best model saved! (Val Acc: {val_acc:.2f}%, Val Loss: {avg_val_loss:.4f})")
            else:
                epochs_without_improvement += 1
                print(f"  No improvement for {epochs_without_improvement} epoch(s)")
            
            # Early stopping check
            if epochs_without_improvement >= patience:
                print(f"\n{'='*80}")
                print(f"Early stopping triggered after {epoch+1} epochs")
                print(f"Best validation accuracy: {best_val_acc:.2f}%")
                print(f"{'='*80}")
                break
        
        print(f"\n{'='*80}")
        print("Training Complete!")
        print(f"{'='*80}")
        print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
        print(f"Best Validation Loss: {best_val_loss:.4f}")
        print(f"Model saved to: {save_path}")
        
        return model, history
    
    def evaluate_model(self, model_path, data_dir):
        """
        Evaluate model and generate comprehensive metrics
        
        Args:
            model_path: Path to saved model
            data_dir: Base dataset directory
            
        Returns:
            report: Classification report dictionary
            cm: Confusion matrix
        """
        print(f"\n{'='*80}")
        print("Model Evaluation")
        print(f"{'='*80}")
        
        model = self.create_model()
        
        # Load model checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"Loaded model from epoch {checkpoint.get('epoch', 'unknown')}")
        else:
            model.load_state_dict(checkpoint)
        
        model.eval()
        
        expander = DatasetExpander()
        test_dataset = datasets.ImageFolder(
            os.path.join(data_dir, 'test'),
            transform=expander.get_validation_transforms()
        )
        test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
        
        print(f"Test dataset size: {len(test_dataset)} images")
        
        all_predictions = []
        all_targets = []
        
        print("\nRunning inference on test set...")
        with torch.no_grad():
            for batch_idx, (data, target) in enumerate(test_loader):
                data = data.to(self.device)
                output = model(data)
                _, predicted = torch.max(output, 1)
                
                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend(target.numpy())
                
                if (batch_idx + 1) % 10 == 0:
                    print(f"  Processed {(batch_idx+1)*16}/{len(test_dataset)} images")
        
        # Generate confusion matrix
        cm = confusion_matrix(all_targets, all_predictions)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=self.class_names, yticklabels=self.class_names)
        plt.title('Confusion Matrix - Test Set', fontsize=14, fontweight='bold')
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        print("\n✓ Confusion matrix saved to: confusion_matrix.png")
        plt.close()
        
        # Generate classification report
        report = classification_report(all_targets, all_predictions, 
                                     target_names=self.class_names, output_dict=True)
        
        print(f"\n{'='*80}")
        print("Evaluation Complete!")
        print(f"{'='*80}")
        
        return report, cm