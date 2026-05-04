#!/usr/bin/env python3
"""
Dataset Folder Renaming Script
Renames extended training/validation folder names to match test folder class names
Maps: adenocarcinoma_left.lower.lobe_T2_N0_M0_Ib → adenocarcinoma
"""

import os
import shutil
from pathlib import Path

# Mapping of extended names to base cancer types
CLASS_NAME_MAPPING = {
    'adenocarcinoma_left.lower.lobe_T2_N0_M0_Ib': 'adenocarcinoma',
    'large.cell.carcinoma_left.hilum_T2_N2_M0_IIIa': 'large.cell.carcinoma',
    'squamous.cell.carcinoma_left.hilum_T1_N2_M0_IIIa': 'squamous.cell.carcinoma',
    'normal': 'normal'  # Already correct
}

def rename_dataset_folders(base_dir='DATASET'):
    """
    Rename training and validation folders to match test folder structure
    
    Args:
        base_dir: Base dataset directory (default: 'DATASET')
    """
    print("=" * 70)
    print("Dataset Folder Renaming Script")
    print("=" * 70)
    
    if not os.path.exists(base_dir):
        print(f"❌ Error: Dataset directory '{base_dir}' not found!")
        return False
    
    # Process train and valid directories
    for split in ['train', 'valid']:
        split_path = os.path.join(base_dir, split)
        
        if not os.path.exists(split_path):
            print(f"⚠️  Warning: '{split}' directory not found, skipping...")
            continue
        
        print(f"\n📁 Processing {split.upper()} directory...")
        print("-" * 70)
        
        # Get all subdirectories
        subdirs = [d for d in os.listdir(split_path) 
                   if os.path.isdir(os.path.join(split_path, d))]
        
        renamed_count = 0
        
        for old_name in subdirs:
            old_path = os.path.join(split_path, old_name)
            
            # Check if folder needs renaming
            if old_name in CLASS_NAME_MAPPING:
                new_name = CLASS_NAME_MAPPING[old_name]
                new_path = os.path.join(split_path, new_name)
                
                # Skip if already correctly named
                if old_name == new_name:
                    print(f"✓ '{old_name}' - Already correct")
                    continue
                
                # Check if target already exists
                if os.path.exists(new_path):
                    print(f"⚠️  '{new_name}' already exists, merging folders...")
                    # Move files from old to new
                    for file in os.listdir(old_path):
                        src = os.path.join(old_path, file)
                        dst = os.path.join(new_path, file)
                        shutil.move(src, dst)
                    # Remove old directory
                    os.rmdir(old_path)
                    print(f"✓ Merged '{old_name}' → '{new_name}'")
                else:
                    # Simple rename
                    os.rename(old_path, new_path)
                    print(f"✓ Renamed: '{old_name}' → '{new_name}'")
                
                renamed_count += 1
            else:
                print(f"⚠️  Unknown folder: '{old_name}' (not in mapping)")
        
        print(f"\n📊 {split.upper()} Summary: {renamed_count} folder(s) renamed")
    
    # Verify final structure
    print("\n" + "=" * 70)
    print("Verification: Final Dataset Structure")
    print("=" * 70)
    
    for split in ['train', 'valid', 'test']:
        split_path = os.path.join(base_dir, split)
        if os.path.exists(split_path):
            subdirs = sorted([d for d in os.listdir(split_path) 
                            if os.path.isdir(os.path.join(split_path, d))])
            print(f"\n{split.upper()}:")
            for subdir in subdirs:
                file_count = len([f for f in os.listdir(os.path.join(split_path, subdir)) 
                                if os.path.isfile(os.path.join(split_path, subdir, f))])
                print(f"  ✓ {subdir:<30} ({file_count} images)")
    
    print("\n" + "=" * 70)
    print("✅ Dataset renaming completed successfully!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = rename_dataset_folders()
    if not success:
        exit(1)
