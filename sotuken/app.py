from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from logic import control as con
from logic import spl as db
from logic.face_auth_core import face_auth_bp, TOLERANCE_THRESHOLD
from werkzeug.utils import secure_filename
from logic.file_ops import move_upload_temp_to_user
import time,os
import shutil #ファイルを移動させるライブラリ

app = Flask(__name__)
app.register_blueprint(face_auth_bp)
app.secret_key = "super_secret_key"

MAX_ATTEMPTS = 3
LOCKOUT_TIME = 30
attempts = 0
lock_until = 0

# ---------------------------------
# ホーム
# ---------------------------------
@app.route("/")
def home():
    # ★ログインしている場合は user_id / username を渡す
    if "user_id" in session and "username" in session:
        return render_template(
            "home.html",
            user_id=session["user_id"],
            username=session["username"]
        )
    return render_template("index.html")

# ---------------------------------
# 顔認証ページ
# ---------------------------------
@app.route("/face_page")
def face_page():
    return render_template("face.html",tolerance = TOLERANCE_THRESHOLD, message=None)

@app.route("/face_auth", methods=["POST"])
def face_auth():
    
    return redirect(url_for("login_page"))

# ---------------------------------
# ログインページ
# ---------------------------------
@app.route("/login_page")
def login_page():
    return render_template("login.html", message=None)

@app.route("/login", methods=["POST"])
def login():
    global attempts, lock_until

    userid = request.form.get("id")
    input_password = request.form.get("password")
    now = time.time()

    if not userid.isdigit():
        return render_template("login.html", message="IDは数値で入力してください")
    userid = int(userid)

    if now < lock_until:
        remaining = int(lock_until - now)
        return render_template(
            "login.html",
            message=f"🚨 ロック中です。あと {remaining} 秒お待ちください。"
        )

    user = db.get_user(userid)  # ★追加（ユーザー名取得）
    if user and db.authenticate_user(userid, input_password):
        attempts = 0
        con.log_event("🟢 ログイン成功")

        # ★ユーザー情報を session に保存
        session["user_id"] = user.id
        session["username"] = user.username

        return redirect("/")  # ★home に戻す

    attempts += 1
    con.log_event(f"⚠️ アクセス回数 ({attempts}/{MAX_ATTEMPTS})")

    if attempts >= MAX_ATTEMPTS:
        lock_until = time.time() + LOCKOUT_TIME
        attempts = 0
        return render_template(
            "login.html",
            message=f"🚨 最大試行回数を超えました。{LOCKOUT_TIME} 秒後に再試行できます。"
        )

    return render_template("login.html", message="IDまたはパスワードが違います")

# ---------------------------------
# 登録ページ
# ---------------------------------
@app.route("/register_page", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        face_file = request.files.getlist("face_file")
        username = request.form.get("full_name")
        password = request.form.get("password")

        if not face_file or not username or not password:
            return render_template("register.html", message="全ての欄を入力してください。")
        
# 空ファイル対策
        face_file = [f for f in face_file if f.filename]
        if not face_file:
            return render_template("register.html", message="画像を選択してください。")

        # ★ここ追加：名前の重複チェック
        existing_user = db.get_user_by_name(username)
        if existing_user:
            return render_template("register.html", message="⚠️ その名前は既に存在しています")

        user = db.create_user(username, password)
        if not user:
            return "⚠️ ユーザー登録に失敗しました"

        if not db.authenticate_user(user.id, password):
            return "⚠️ パスワード保存に問題があります"
        
        # 一時保存フォルダ
        upload_dir = "upload_temp"

        filenames = []

        for f in face_file:
            filename = secure_filename(f.filename)
            save_path = os.path.join(upload_dir, filename)
            f.save(save_path)
            filenames.append(filename)

        session["registration"] = {
            "full_name": username,
            "face_file": filenames,
            "password": password,
            "id": user.id
        }

 # セッションからIDの取得
        user_id = user.id
        os.makedirs(f'picture/{user_id}', exist_ok=True)
 # print(f"+++++作成したパス{filepass}+++++")
        return redirect("/register_confirm")

    return render_template("register.html", message=None)

@app.route("/register_confirm", methods=["GET", "POST"])
def register_confirm():
    data = session.get("registration")
    if not data:
        return redirect("/register_page")
    
    if request.method == "POST":
        user_id = data["id"]
        move_upload_temp_to_user(user_id)
        return redirect("/")
    
    return render_template("register_confirm.html", data=data)

#Egg追加
@app.route("/temp_image/<filename>")
def temp_image(filename):
    return send_from_directory("upload_temp",filename)

# ---------------------------------
# ログアウト
# ---------------------------------
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()  # セッション情報をすべて削除
    return redirect("/")  # トップページへ戻す

# ---------------------------------
# アカウント削除処理
# ---------------------------------
@app.route("/delete", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect("/login_page")

    user_id = session["user_id"]

    if db.delete_user(user_id):   # ← DB削除
        db.delete_user_picture(user_id)  # ← フォルダ削除
        session.clear()
        return render_template("delete_done.html")  # 完了ページへ
    else:
        return "削除に失敗しました…"


# ---------------------------------
# 削除確認
# ---------------------------------
@app.route("/delete_confirm_page")
def delete_confirm_page():
    if "user_id" not in session:
        return redirect("/login_page")

    user = db.get_user(session["user_id"])
    return render_template("delete_confirm.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)