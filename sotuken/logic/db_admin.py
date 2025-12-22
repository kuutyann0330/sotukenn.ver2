#データベース管理
import tkinter as tk
from tkinter import messagebox
import sqlite3

DB_NAME = "faces.db"


def search_face(id_text: str, name: str, result_label):
    """ID、名前、または両方でデータを検索"""
    if not id_text and not name:
        messagebox.showerror("エラー", "ID または 名前を入力してください。")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # --- 検索条件を動的に構築 ---
        query = "SELECT id, name FROM faces WHERE 1=1"
        params = []

        if id_text:
            query += " AND id = ?"
            params.append(id_text)
        if name:
            query += " AND name = ?"
            params.append(name)

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        if not rows:
            result_label.config(text="データは見つかりません。", fg="red")
        else:
            text = "\n".join([f"ID: {r[0]} / 名前: {r[1]}" for r in rows])
            result_label.config(text=f"検索結果:\n{text}", fg="green")

    except Exception as e:
        messagebox.showerror("エラー", f"検索中にエラーが発生しました:\n{e}")


def delete_face(id_text: str, name: str, result_label):
    """指定したIDまたは名前のデータを削除（両方一致も可）"""
    if not id_text and not name:
        messagebox.showerror("エラー", "ID または 名前を入力してください。")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # --- 削除対象の確認 ---
        query = "SELECT id, name FROM faces WHERE 1=1"
        params = []
        if id_text:
            query += " AND id = ?"
            params.append(id_text)
        if name:
            query += " AND name = ?"
            params.append(name)

        c.execute(query, params)
        rows = c.fetchall()

        if not rows:
            messagebox.showinfo("結果", "対象データは存在しません。")
            conn.close()
            return

        confirm_text = f"{len(rows)}件のデータを削除しますか？\n"
        confirm_text += "\n".join([f"ID:{r[0]} / 名前:{r[1]}" for r in rows])
        if not messagebox.askyesno("確認", confirm_text):
            conn.close()
            return

        # --- 削除実行 ---
        delete_query = "DELETE FROM faces WHERE 1=1"
        delete_params = []
        if id_text:
            delete_query += " AND id = ?"
            delete_params.append(id_text)
        if name:
            delete_query += " AND name = ?"
            delete_params.append(name)

        c.execute(delete_query, delete_params)
        conn.commit()
        conn.close()

        result_label.config(text="データを削除しました。", fg="blue")
        messagebox.showinfo("完了", "データを削除しました。")

    except Exception as e:
        messagebox.showerror("エラー", f"削除中にエラーが発生しました:\n{e}")


# ===== GUI 作成 =====
root = tk.Tk()
root.title("顔データ検索・削除")
root.geometry("420x280")

# ID入力欄
tk.Label(root, text="IDを入力:").pack(pady=(10, 0))
entry_id = tk.Entry(root, width=40)
entry_id.pack(pady=5)

# 名前入力欄
tk.Label(root, text="名前を入力:").pack(pady=(10, 0))
entry_name = tk.Entry(root, width=40)
entry_name.pack(pady=5)

# 結果表示ラベル
result_label = tk.Label(root, text="", fg="gray", justify="left")
result_label.pack(pady=5)

# ボタン群
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(
    frame, text="検索", width=10,
    command=lambda: search_face(entry_id.get().strip(), entry_name.get().strip(), result_label)
).grid(row=0, column=0, padx=5)

tk.Button(
    frame, text="削除", width=10,
    command=lambda: delete_face(entry_id.get().strip(), entry_name.get().strip(), result_label)
).grid(row=0, column=1, padx=5)

tk.Button(root, text="終了", command=root.quit).pack(pady=10)

root.mainloop()
