#顔特徴量の生成。
import face_recognition
import io
from PIL import Image
import numpy as np

def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    """
    復号済み画像データ（bytes）から顔特徴量を生成して返す
    """
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    encodings = face_recognition.face_encodings(img_array)
    if not encodings:
        raise ValueError("顔が検出できませんでした")
    return encodings[0]  # 1枚の画像につき1つの顔特徴量を返す