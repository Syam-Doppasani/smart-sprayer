"""
Split the agri_data into train/val folders (80/20) for YOLO training.
Creates: data/dataset/train/images, data/dataset/train/labels,
         data/dataset/val/images, data/dataset/val/labels
Also generates data/dataset/data.yaml
"""
import os
import shutil
import random

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..", "data", "agri_data", "data")
OUT_DIR = os.path.join(BASE_DIR, "..", "data", "dataset")

SPLIT_RATIO = 0.8  # 80% train, 20% val

def main():
    # Collect all image files that have a matching label
    images = sorted([f for f in os.listdir(SRC_DIR) if f.endswith((".jpeg", ".jpg", ".png"))])
    paired = []
    for img in images:
        name = os.path.splitext(img)[0]
        label = name + ".txt"
        if os.path.exists(os.path.join(SRC_DIR, label)):
            paired.append((img, label))

    print(f"Found {len(paired)} image-label pairs")

    random.shuffle(paired)
    split_idx = int(len(paired) * SPLIT_RATIO)
    train_set = paired[:split_idx]
    val_set = paired[split_idx:]

    print(f"Train: {len(train_set)}, Val: {len(val_set)}")

    # Create output directories
    for split in ["train", "val"]:
        for sub in ["images", "labels"]:
            d = os.path.join(OUT_DIR, split, sub)
            os.makedirs(d, exist_ok=True)

    # Copy files
    def copy_files(file_list, split_name):
        for img_file, lbl_file in file_list:
            shutil.copy2(os.path.join(SRC_DIR, img_file), os.path.join(OUT_DIR, split_name, "images", img_file))
            shutil.copy2(os.path.join(SRC_DIR, lbl_file), os.path.join(OUT_DIR, split_name, "labels", lbl_file))

    copy_files(train_set, "train")
    copy_files(val_set, "val")

    # Generate data.yaml
    yaml_path = os.path.join(OUT_DIR, "data.yaml")
    abs_out = os.path.abspath(OUT_DIR).replace("\\", "/")
    with open(yaml_path, "w") as f:
        f.write(f"path: {abs_out}\n")
        f.write("train: train/images\n")
        f.write("val: val/images\n")
        f.write("\n")
        f.write("nc: 1\n")
        f.write("names: ['plant']\n")

    print(f"✅ Dataset split complete!")
    print(f"   Train: {len(train_set)} images")
    print(f"   Val:   {len(val_set)} images")
    print(f"   data.yaml: {yaml_path}")

if __name__ == "__main__":
    main()
