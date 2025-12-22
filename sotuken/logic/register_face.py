# 暗号化とDB登録（パスワード付き）
import sqlite3
import bcrypt
from crypto_utils import encrypt_bytes

DB_NAME = "faces.db"

def register_user(name: str, password: str):
    """ユーザーを登録（パスワードをハッシュ化して保存）"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # bcryptで安全にパスワードをハッシュ化
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    c.execute("INSERT INTO users (name, password_hash) VALUES (?, ?)", (name, hashed_pw))
    user_id = c.lastrowid
    conn.commit()
    conn.close()

    print(f"ユーザー '{name}' (ID: {user_id}) を登録しました。")
    return user_id


def register_face(user_id: int, image_path: str):
    """顔画像を暗号化してDBに登録"""
    with open(image_path, "rb") as f:
        raw_data = f.read()

    # 暗号化
    enc_data = encrypt_bytes(raw_data)

    # DBに登録
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO faces (user_id, face_data) VALUES (?, ?)", (user_id, enc_data))
    face_id = c.lastrowid
    conn.commit()
    conn.close()

    print(f"ユーザーID {user_id} の顔画像 (Face ID: {face_id}) を登録しました。")

    # ID と暗号化データを返す
    return face_id, enc_data


if __name__ == "__main__":
    name = input("ユーザー名を入力してください: ")
    password = input("パスワードを入力してください: ")
    image_path = input("登録する画像のパスを入力してください: ")

    # 1️⃣ ユーザーを登録
    user_id = register_user(name, password)

    # 2️⃣ そのユーザーに顔画像を登録
    register_face(user_id, image_path)