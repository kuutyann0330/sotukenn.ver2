# 暗号化・複合化　モジュール
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# AES鍵（16, 24, 32バイトで設定可能）
KEY = b"this_is_my_key16"

def encrypt_bytes(data: bytes) -> bytes:  #暗号化
    cipher = AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes

def decrypt_bytes(enc_data: bytes) -> bytes:  #複号化
    iv = enc_data[:16]
    ct = enc_data[16:]
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)
