# secure_decrypt_with_monitor.py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
import os
import sys
import getpass
import socket
import time
import bcrypt

# ==============================
# 設定
# ==============================
MAX_ATTEMPTS = 3
LOCKOUT_TIME = 30
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# パスワードハッシュ化（実運用では外部に保存・DB管理推奨）
# 元のパスワード: "MyStrongPassword123"
CORRECT_PASSWORD_HASH = bcrypt.hashpw(b"MyStrongPassword123", bcrypt.gensalt())

# AES鍵（16, 24, 32 bytes）
KEY = b"thisisasecretkey16"

# 入出力ファイル
INPUT_PATH = "encrypted_image.bin"
OUTPUT_PATH = "restored_image.png"

# ==============================
# 関数定義
# ==============================

def log_event(message):
    """アクセスログを日付ごとに記録"""
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(LOG_DIR, f"access_{date_str}.txt")
    user = os.getenv("USERNAME") or os.getenv("USER") or "unknown_user"
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "unknown_ip"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] User={user} IP={ip} | {message}\n")

def authenticate_user():
    """ユーザー認証 + 試行制限"""
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            password = getpass.getpass("アクセスパスワードを入力してください: ")
        except Exception:
            password = input("アクセスパスワードを入力してください（表示されます）: ")

        if bcrypt.checkpw(password.encode(), CORRECT_PASSWORD_HASH):
            log_event("✅ 認証成功。")
            return True
        else:
            attempts += 1
            print("🚫 パスワードが間違っています。")
            log_event(f"⚠️ 不正アクセス試行 ({attempts}/{MAX_ATTEMPTS})")

            if attempts >= MAX_ATTEMPTS:
                print(f"🚨 不正アクセスを検出！システムをロックします（{LOCKOUT_TIME}秒）")
                log_event("🚨 最大試行回数を超過。アクセスがロックされました。")
                time.sleep(LOCKOUT_TIME)
                raise PermissionError("最大試行回数を超過しました。")

    return False

def decrypt_image_secure(input_path, output_path):
    """安全なAES復号処理（IVをファイル先頭に含む）"""
    if not authenticate_user():
        print("認証に失敗しました。")
        return

    if not os.path.exists(input_path):
        print(f"入力ファイルが見つかりません: {input_path}")
        log_event(f"❌ 復号失敗：入力ファイルが見つからない ({input_path})")
        return

    try:
        with open(input_path, "rb") as f:
            iv = f.read(16)  # 先頭16バイトがIV
            encrypted_data = f.read()

        cipher = AES.new(KEY, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        with open(output_path, "wb") as f:
            f.write(decrypted)

        print(f"[OK] 復号完了: {output_path}")
        log_event(f"✅ 復号成功: {output_path}")

    except (ValueError, KeyError) as e:
        print("🚫 復号に失敗しました（データ破損またはキー/IV不一致）。")
        log_event(f"❌ 復号失敗：{str(e)}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        log_event(f"❌ 復号中エラー：{str(e)}")

# ==============================
# メイン処理
# ==============================
if __name__ == "__main__":
    try:
        decrypt_image_secure(INPUT_PATH, OUTPUT_PATH)
    except PermissionError as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⛔ 処理が中断されました。")
        log_event("⚠️ ユーザーが復号処理を中断しました。")
    except Exception as e:
        print(f"エラー: {e}")
        log_event(f"❌ 致命的エラー：{e}")
