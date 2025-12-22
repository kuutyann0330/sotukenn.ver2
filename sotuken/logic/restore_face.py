import sqlite3
from crypto_utils import decrypt_bytes
from face_utils import get_face_embedding  # 顔特徴量生成用
import gc

DB_NAME = "faces.db"

def restore_all_face_embeddings() -> dict:
    """
    DB内のすべての顔データを復号して
    {user_id: 顔特徴量(numpy配列)} の辞書として返す
    名前指定なし、比較は行わない
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, face_data FROM faces")
    rows = c.fetchall()
    conn.close()

    embeddings = {}
    for user_id, enc_data in rows:
        try:
            decrypted_data = decrypt_bytes(enc_data)  # 暗号化データを復号
            embedding = get_face_embedding(decrypted_data)  # 特徴量取得
            embeddings[user_id] = embedding
        except Exception as e:
            print(f"ユーザー {user_id} の復号・特徴量取得に失敗: {e}")
        finally:
            # メモリ解放
            del decrypted_data
            gc.collect()

    return embeddings

if __name__ == "__main__":
    all_embeddings = restore_all_face_embeddings()
    print(f"{len(all_embeddings)} 件の顔データを復号しました")