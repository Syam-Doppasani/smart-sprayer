import os

def convert_to_single_class(label_dir):
    for file in os.listdir(label_dir):
        if not file.endswith(".txt"):
            continue
        path = os.path.join(label_dir, file)

        with open(path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            parts[0] = "0"  # force class = plant
            new_lines.append(" ".join(parts) + "\n")

        with open(path, "w") as f:
            f.writelines(new_lines)

# Run for all splits
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base = os.path.join(BASE_DIR, "..", "data", "WeedCrop.v1i.yolov5pytorch")

convert_to_single_class(os.path.join(base, "train", "labels"))
convert_to_single_class(os.path.join(base, "valid", "labels"))
convert_to_single_class(os.path.join(base, "test", "labels"))

print("✅ Labels converted to single class")