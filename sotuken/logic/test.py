import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from register_face import register_face, register_user
from restore_face import restore_all_face_embeddings
import gc
import os
import tempfile
import subprocess
import platform
import shutil

# ===== ファイル選択 =====
def select_files():
    """複数画像を選択"""
    file_paths = filedialog.askopenfilenames(
        title="顔画像を選択",
        filetypes=[("画像ファイル", "*.jpg *.jpeg *.png")]
    )
    if file_paths:
        entry_files.delete(0, tk.END)
        entry_files.insert(0, "; ".join(file_paths))

# ===== パスワード表示切替 =====
def toggle_password():
    if entry_password.cget("show") == "":
        entry_password.config(show="*")
        btn_toggle_pw.config(text="👁")
    else:
        entry_password.config(show="")
        btn_toggle_pw.config(text="🙈")

# ===== OSに応じて画像を開く =====
def open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("エラー", f"ファイルを開けませんでした: {e}")

# ===== 登録前確認ダイアログ =====
def show_confirmation_dialog(name, password, image_paths):
    confirm_win = Toplevel(root)
    confirm_win.title("登録内容の確認")
    confirm_win.geometry("420x400")
    confirm_win.grab_set()

    tk.Label(confirm_win, text="以下の内容で登録しますか？", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(confirm_win, text=f"名前: {name}", anchor="w").pack(fill="x", padx=20, pady=5)

    # パスワード表示切替
    pw_frame = tk.Frame(confirm_win)
    pw_frame.pack(pady=5)
    pw_label = tk.Label(pw_frame, text="パスワード: " + "●" * len(password))
    pw_label.pack(side="left")

    def toggle_pw_in_confirm():
        if pw_label.cget("text").startswith("パスワード: ●"):
            pw_label.config(text=f"パスワード: {password}")
            btn_toggle_pw2.config(text="🙈")
        else:
            pw_label.config(text="パスワード: " + "●" * len(password))
            btn_toggle_pw2.config(text="👁")

    btn_toggle_pw2 = tk.Button(pw_frame, text="👁", width=2, command=toggle_pw_in_confirm)
    btn_toggle_pw2.pack(side="left", padx=5)

    # ファイル一覧
    tk.Label(confirm_win, text="選択したファイル:", anchor="w").pack(fill="x", padx=20, pady=(10,0))
    file_frame = tk.Frame(confirm_win)
    file_frame.pack(fill="both", expand=True, padx=20, pady=5)

    listbox = tk.Listbox(file_frame, height=6)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar = tk.Scrollbar(file_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)

    for img_path in image_paths:
        listbox.insert(tk.END, os.path.basename(img_path))

    # 一時ファイルリスト（確認用コピー）
    temp_files = []

    def open_selected():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("確認", "確認したいファイルを選択してください。")
            return

        original_path = image_paths[selected[0]]
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, os.path.basename(original_path))

        # 一時コピー作成
        shutil.copy2(original_path, temp_path)
        temp_files.append(temp_path)
        open_file(temp_path)

    tk.Button(confirm_win, text="選択したファイルを開く", command=open_selected).pack(pady=5)

    # 登録処理
    def confirm():
        confirm_win.destroy()
        register_process(name, password, image_paths)

    tk.Button(confirm_win, text="登録する", bg="#4CAF50", fg="white", command=confirm).pack(pady=10)

    # キャンセル時は一時ファイル削除
    def on_close():
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        confirm_win.destroy()

    tk.Button(confirm_win, text="キャンセル", command=on_close).pack()
    confirm_win.protocol("WM_DELETE_WINDOW", on_close)

# ===== 実際の登録処理 =====
def register_process(name, password, image_paths):
    try:
        user_id = register_user(name, password)
    except Exception as e:
        messagebox.showerror("エラー", f"ユーザー登録に失敗しました: {e}")
        return

    face_count = 0
    for img_path in image_paths:
        try:
            user_id, enc_data = register_face(user_id, img_path)
            face_count += 1
        except Exception as e:
            messagebox.showwarning("警告", f"{os.path.basename(img_path)} の登録に失敗しました: {e}")

    face_dict = restore_all_face_embeddings()
    if face_dict:
        msg = f"{name} さんを登録しました。\n登録画像数: {face_count}\nDB内の総データ件数: {len(face_dict)}"
        messagebox.showinfo("結果", msg)
    else:
        messagebox.showerror("結果", "DBから復号データを取得できませんでした。")

    del face_dict
    gc.collect()

# ===== 実行前チェック =====
def run_test():
    image_paths = entry_files.get().split("; ")
    name = entry_name.get().strip()
    password = entry_password.get().strip()

    if not image_paths or not all(os.path.exists(p) for p in image_paths):
        messagebox.showerror("エラー", "有効な画像ファイルを選択してください")
        return
    if not name:
        messagebox.showerror("エラー", "名前を入力してください")
        return
    if not password:
        messagebox.showerror("エラー", "パスワードを入力してください")
        return

    show_confirmation_dialog(name, password, image_paths)

# ===== GUI作成 =====
root = tk.Tk()
root.title("顔画像登録テスト（確認画面・安全版）")

tk.Label(root, text="顔画像ファイル（複数可）:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_files = tk.Entry(root, width=50)
entry_files.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="参照", command=select_files).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="名前:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_name = tk.Entry(root, width=50)
entry_name.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="パスワード:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
pw_frame = tk.Frame(root)
pw_frame.grid(row=2, column=1, padx=5, pady=5)
entry_password = tk.Entry(pw_frame, width=47, show="*")
entry_password.pack(side="left")
btn_toggle_pw = tk.Button(pw_frame, text="👁", width=2, command=toggle_password)
btn_toggle_pw.pack(side="left", padx=3)

tk.Button(root, text="登録＆テスト", command=run_test, bg="#4CAF50", fg="white").grid(row=3, column=1, pady=10)

root.mainloop()