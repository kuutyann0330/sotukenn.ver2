#テーブル作成用
import sqlite3

DB_NAME = "faces.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ユーザー情報テーブル（パスワードを追加）
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')

    # 顔画像テーブル（ユーザーIDと紐づく）
    c.execute('''
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        face_data BLOB NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"データベース '{DB_NAME}' を作成しました。")

if __name__ == "__main__":
    create_database()