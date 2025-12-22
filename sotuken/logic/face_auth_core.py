import cv2
import os
import time
import secrets
import numpy as np
import face_recognition

from flask import (
    Blueprint, Response,
    render_template, jsonify,
    session, redirect
)

from PIL import Image, ImageDraw, ImageFont
from logic import spl as db

# ===============================
# 定数
# ===============================
TOLERANCE_THRESHOLD = 1
FAIL_TIMEOUT = 3
MAX_SUCCESS_FRAMES = 15
FONT_PATH = "C:/Windows/Fonts/meiryo.ttc"

# ===============================
# グローバル認証状態
# ===============================
AUTH_STATES = {}


class FaceAuthState:
    def __init__(self):
        self.authenticated = False
        self.username = "未確認"
        self.success_frames = 0
        self.face_detected = False
        self.face_detected_time = None
        self.failed = False


# ===============================
# 認証状態取得（混線防止の核）
# ===============================
def get_auth_state():
    sid = session.get("auth_sid")

    if not sid:
        sid = secrets.token_hex(16) #ここでauth_sidを生成している
        session["auth_sid"] = sid

    if sid not in AUTH_STATES:
        AUTH_STATES[sid] = FaceAuthState()

    return AUTH_STATES[sid]


def clear_auth_state():
    sid = session.get("auth_sid")
    if sid:
        AUTH_STATES.pop(sid, None)
    session.clear()


# ===============================
# 顔データロード
# ===============================
def load_known_faces():
    encodings, names = [], []

    for root, _, files in os.walk("picture"):
        person = os.path.basename(root)
        if person == "picture":
            continue

        for f in files:
            if f.lower().endswith((".jpg", ".png")):
                img = face_recognition.load_image_file(os.path.join(root, f))
                enc = face_recognition.face_encodings(img)
                if enc:
                    encodings.append(enc[0])
                    names.append(person)

    return encodings, names


# ===============================
# Blueprint
# ===============================
face_auth_bp = Blueprint(
    "face_auth",
    __name__,
    template_folder="../templates"
)

# ===============================
# カメラストリーム
# ===============================
def generate_frames(auth_sid):
    # state = get_auth_state()
    if auth_sid not in AUTH_STATES:
        AUTH_STATES[auth_sid] = FaceAuthState()
    state = AUTH_STATES[auth_sid]
    known_encodings, known_names = load_known_faces()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return

    font = ImageFont.truetype(FONT_PATH, 20)
    frame_count = 0

    try:
        while True:
            if state.authenticated and state.success_frames >= MAX_SUCCESS_FRAMES:
                break

            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 3 == 0 and not state.authenticated:
                small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

                locations = face_recognition.face_locations(rgb)
                encodings = face_recognition.face_encodings(rgb, locations)

                if locations and not state.face_detected:
                    state.face_detected = True
                    state.face_detected_time = time.time()

                names = []
                for enc in encodings:
                    name = "未確認"
                    if known_encodings:
                        dist = face_recognition.face_distance(known_encodings, enc)
                        idx = np.argmin(dist)
                        if dist[idx] < TOLERANCE_THRESHOLD:
                            name = known_names[idx]
                            state.authenticated = True
                            state.username = name
                    names.append(name)

                saved_locations = locations
                saved_names = names

            if "saved_locations" in locals():
                pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil)

                for (t, r, b, l), name in zip(saved_locations, saved_names):
                    t *= 4; r *= 4; b *= 4; l *= 4
                    color = (0, 255, 0) if name != "未確認" else (255, 0, 0)
                    cv2.rectangle(frame, (l, t), (r, b), color, 2)
                    draw.text((l + 6, b - 28), name, font=font, fill=(255, 255, 255))

                frame = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

            if state.authenticated:
                state.success_frames += 1

            if state.face_detected and not state.authenticated:
                if time.time() - state.face_detected_time > FAIL_TIMEOUT:
                    state.failed = True
                    clear_auth_state()
                    break

            ret, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

            frame_count += 1

    finally:
        cap.release()
        cv2.destroyAllWindows()


# ===============================
# Routes
# ===============================
@face_auth_bp.route("/face_recognition_page")
def face_recognition_page():
    return render_template("Face_recognition.html")


@face_auth_bp.route("/video_feed")
def video_feed():
 # コンテキストが生きているここで session を操作する
    sid = session.get("auth_sid")
    if not sid:
        sid = secrets.token_hex(16)
        session["auth_sid"] = sid
    
    if sid not in AUTH_STATES:
        AUTH_STATES[sid] = FaceAuthState()
    else:
        # 開始時にリセット
        AUTH_STATES[sid] = FaceAuthState()

    return Response(
        generate_frames(sid), # 引数として sid を渡す
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@face_auth_bp.route("/auth_status")
def auth_status():
    sid = session.get("auth_sid")
    state = AUTH_STATES.get(sid)

    if not state:
        return jsonify({"status": "unauthenticated"})

    # 認証成功時の処理
    if state.authenticated and state.success_frames >= MAX_SUCCESS_FRAMES:
        # ここは「リクエストコンテキスト内」なのでsessionが使える
        user = db.get_user_by_name(state.username)
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            return jsonify({
                "status": "authenticated",
                "username": user.username,
                "redirect_url": "/"
            })

    # 失敗時の処理
    if state.failed:
        AUTH_STATES.pop(sid, None)
        return jsonify({
            "status": "failed",
            "redirect_url": "/face_page" # 再試行のためにリダイレクト
        })

    return jsonify({"status": "unauthenticated"})


@face_auth_bp.route("/delete_account", methods=["POST"])
def delete_account():
    user_id = session.get("user_id")
    if user_id:
        db.delete_user(user_id)

    clear_auth_state()
    return redirect("/login_page")
