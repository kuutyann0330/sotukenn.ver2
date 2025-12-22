# decrypt_with_monitor.py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
import os
import sys
import socket
import time

# === access_monitor から持ってくる設定と関数（または access_monitor.py を同ディレクトリに置いて import してもよい） ===
MAX_ATTEMPTS = 3
LOCKOUT_TIME = 30
LOG_FILE = "access_log.txt"

def log_event(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        user = os.getenv("USERNAME") or os.getenv("USER") or "unknown_user"
        # IP の取り方は環境で変わるので例示的に取得
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "unknown_ip"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] User={user} IP={ip} | {message}\n")

def authenticate_user(userpassword,CORRECT_PASSWORD):
    attempts = 0
    if attempts < MAX_ATTEMPTS:
        if userpassword == CORRECT_PASSWORD:
            print("✅ 認証成功。")
            log_event("✅ 認証成功。")
            return True
        else:
            attempts += 1
            print("🚫 パスワードが間違っています。")
            log_event(f"⚠️ アクセス回数 ({attempts}/{MAX_ATTEMPTS})")

            if attempts >= MAX_ATTEMPTS:
                print(f"🚨 不正アクセスを検出！アカウントをロックします（{LOCKOUT_TIME}秒）")
                log_event("🚨 最大試行回数を超過。アクセスがロックされました。")
                time.sleep(LOCKOUT_TIME)
                # プロセス終了（必要に応じて例外に変える）
                sys.exit(1)

    return False

# # === AES 設定（例） ===
# key = b"thisisasecretkey"     # 16/24/32 bytes
# iv = b"thisisasecretkey"      # 16 bytes

# input_path = "encrypted_image.bin"   # 復号したいファイル（入力）
# output_path = "restored_image.png"   # 復号した結果を保存（出力）

# # === 復号処理 ===
# def decrypt_image_secure(input_path, output_path):
#     # 1) まず認証する
#     if not authenticate_user():
#         # authenticate_user が False を返す場合（通常は上で sys.exit している）
#         print("認証に失敗しました。")
#         return

#     # 認証成功 -> 復号を試みる
#     try:
#         with open(input_path, "rb") as f:
#             encrypted_data = f.read()
#     except FileNotFoundError:
#         print(f"入力ファイルが見つかりません: {input_path}")
#         log_event(f"❌ 復号失敗：入力ファイルが見つからない ({input_path})")
#         return

#     try:
#         cipher = AES.new(key, AES.MODE_CBC, iv)
#         decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
#     except (ValueError, KeyError) as e:
#         # ValueError はパディング不正（＝間違ったキー/IV/破損）など
#         print("🚫 復号に失敗しました（データが破損しているか、キー/IV/パスワードが正しくありません）。")
#         log_event(f"❌ 復号失敗：{str(e)}")
#         return

#     with open(output_path, "wb") as f:
#         f.write(decrypted)

#     print(f"[OK] 復号完了: {output_path}")
#     log_event(f"✅ 復号成功: {output_path}")

# if __name__ == "__main__":
#     decrypt_image_secure(input_path, output_path)
