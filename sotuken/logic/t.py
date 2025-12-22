from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

# ===== 設定 =====
key = b"thisisasecretkey"  # 16, 24, 32バイトのみ有効（AES-128, AES-192, AES-256）
iv = b"thisisaninitvect"   # 16バイト固定（IV: 初期ベクトル）

# ===== 暗号化関数 =====
def encrypt_image(input_path, output_path):
    with open(input_path, "rb") as f:
        data = f.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data, AES.block_size))

    with open(output_path, "wb") as f:
        f.write(encrypted)

    print(f"暗号化完了: {output_path}")

# ===== 実行例 =====
encrypt_image("goldenface.jpg", "encrypted_image.bin")
