import cv2
import mediapipe as mp
import pandas as pd
import os
import yaml

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5
)

DATASET_DIR = r'D:\Syaeful\Kuliah\Semester 4\Dataset\BAHASAKU.yolov8'
CSV_1_TANGAN  = 'dataset/dataset_1tangan.csv'   # C E I J L O R U V Z
CSV_2_TANGAN  = 'dataset/dataset_2tangan.csv'   # Sisanya

# Huruf yang hanya pakai 1 tangan
HURUF_1_TANGAN = {'C', 'E', 'I', 'J', 'L', 'O', 'R', 'U', 'V', 'Z'}

def extract():
    data_1t = []  # Tampung data huruf 1 tangan
    data_2t = []  # Tampung data huruf 2 tangan
    skip_count = 0
    
    yaml_path = os.path.join(DATASET_DIR, 'data.yaml')
    with open(yaml_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    classes = yaml_data.get('names', [])

    for split in ['train', 'valid', 'test']:
        images_dir = os.path.join(DATASET_DIR, split, 'images')
        labels_dir = os.path.join(DATASET_DIR, split, 'labels')

        if not os.path.exists(images_dir):
            continue

        print(f"\nMemproses folder: {split}")

        for img_name in os.listdir(images_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            txt_path = os.path.join(labels_dir, os.path.splitext(img_name)[0] + '.txt')
            if not os.path.exists(txt_path):
                continue

            with open(txt_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    continue
                class_id = int(content.split()[0])
                label = classes[class_id] if class_id < len(classes) else str(class_id)
                label = label.upper()

            img = cv2.imread(os.path.join(images_dir, img_name))
            if img is None:
                continue

            results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if not results.multi_hand_landmarks:
                skip_count += 1
                continue

            jumlah_tangan = len(results.multi_hand_landmarks)

            if label in HURUF_1_TANGAN:
                # ✅ Ambil hanya tangan pertama → 63 fitur
                coords = []
                for lm in results.multi_hand_landmarks[0].landmark:
                    coords.extend([lm.x, lm.y, lm.z])
                coords.append(label)
                data_1t.append(coords)

            else:
                # ✅ Gabungkan 2 tangan → 126 fitur
                # Jika ternyata hanya 1 tangan terdeteksi di gambar 2-tangan,
                # kita SKIP (jangan isi dengan 0, karena data akan misleading)
                if jumlah_tangan < 2:
                    skip_count += 1
                    continue

                coords = []
                for lm in results.multi_hand_landmarks[0].landmark:
                    coords.extend([lm.x, lm.y, lm.z])
                for lm in results.multi_hand_landmarks[1].landmark:
                    coords.extend([lm.x, lm.y, lm.z])
                coords.append(label)
                data_2t.append(coords)

    # Buat kolom CSV
    cols_63  = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + ['label']
    cols_126 = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + \
               [f'{a}{i}_2' for i in range(21) for a in ['x','y','z']] + ['label']

    os.makedirs('dataset', exist_ok=True)

    if data_1t:
        df1 = pd.DataFrame(data_1t, columns=cols_63)
        df1.to_csv(CSV_1_TANGAN, index=False)
        print(f"\n✅ Dataset 1 tangan: {len(data_1t)} sampel")
        print(df1['label'].value_counts().to_string())

    if data_2t:
        df2 = pd.DataFrame(data_2t, columns=cols_126)
        df2.to_csv(CSV_2_TANGAN, index=False)
        print(f"\n✅ Dataset 2 tangan: {len(data_2t)} sampel")
        print(df2['label'].value_counts().to_string())

    print(f"\n⚠️  Total gambar di-skip (tangan tidak terdeteksi): {skip_count}")
    print("    → Ini normal, tapi jika skip > 50% berarti kualitas dataset perlu dicek")

if __name__ == "__main__":
    extract()