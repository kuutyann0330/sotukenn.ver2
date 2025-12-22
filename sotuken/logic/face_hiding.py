import cv2
import numpy as np
import imutils
import threading
import tkinter as tk
from tkinter import messagebox
from collections import deque

# =============================
#  設定パラメータ
# =============================
MOTION_THRESHOLD = 2.0
OCCLUSION_ALERT = 40.0

# =============================
#  関数定義
# =============================
def skin_mask(frame):
    """皮膚色領域マスクを生成（YCbCr空間ベース）"""
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    lower = np.array((0, 133, 77), dtype=np.uint8)
    upper = np.array((255, 173, 127), dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)
    mask = cv2.medianBlur(mask, 5)
    return mask


def compute_occlusion_percent(frame, face_box):
    """顔の隠れ率（%）を推定"""
    (x, y, w, h) = face_box
    face_roi = frame[y:y+h, x:x+w]
    if face_roi.size == 0:
        return 100.0

    mask_skin = skin_mask(face_roi)
    face_area = w * h
    visible_area = np.count_nonzero(mask_skin)
    if face_area == 0:
        return 100.0
    visible_ratio = visible_area / face_area #見えている割合 = 肌色が見えている面積 ÷ 顔の全体面積
    occlusion_percent = (1 - visible_ratio) * 100
    return max(0, min(occlusion_percent, 100))
    
    

# =============================
#  顔認証クラス
# =============================
class FaceAuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("顔認証AIシステム")
        self.root.configure(bg="black")

        # 状態フラグ
        self.running = False
        self.cap = None

        # 顔検出器
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.frame_queue = deque(maxlen=8)
        self.min_visible_ratio = 100.0

        # UI構築
        self.create_widgets()

    def create_widgets(self):
        """GUI構成"""
        self.title_label = tk.Label(self.root, text="顔認証AIシステム", font=("Meiryo", 18, "bold"), fg="white", bg="black")
        self.title_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="待機中...", font=("Meiryo", 14), fg="lightgray", bg="black")
        self.status_label.pack(pady=10)

        self.occlusion_label = tk.Label(self.root, text="", font=("Meiryo", 13), fg="lightgray", bg="black")
        self.occlusion_label.pack(pady=5)

        # ボタン
        btn_frame = tk.Frame(self.root, bg="black")
        btn_frame.pack(pady=15)

        self.btn_register = tk.Button(btn_frame, text="登録", font=("Meiryo", 12),
                                      bg="#222", fg="white", width=10, command=self.register_user)
        self.btn_register.grid(row=0, column=0, padx=10)

        self.btn_start = tk.Button(btn_frame, text="認証開始", font=("Meiryo", 12),
                                   bg="#2e8b57", fg="white", width=10, command=self.start_auth)
        self.btn_start.grid(row=0, column=1, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="終了", font=("Meiryo", 12),
                                  bg="#8b0000", fg="white", width=10, command=self.stop_auth)
        self.btn_stop.grid(row=0, column=2, padx=10)

    def register_user(self):
        """登録ボタン（簡易表示のみ）"""
        messagebox.showinfo("登録", "顔データ登録機能は準備中です。")

    def start_auth(self):
        """認証開始"""
        if self.running:
            return
        self.running = True
        self.status_label.config(text="カメラ起動中...", fg="yellow")
        threading.Thread(target=self.run_camera, daemon=True).start()

    def stop_auth(self):
        """認証終了"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.status_label.config(text="停止しました", fg="lightgray")
    

    def check_motion(self, frame):
        """動きスコアを算出"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frame_queue.append(gray)
        if len(self.frame_queue) < 3:
            return False, 0.0
        diffs = []
        for i in range(1, len(self.frame_queue)):
            diff = cv2.absdiff(self.frame_queue[i], self.frame_queue[i-1])
            diffs.append(np.mean(diff))
        motion_score = float(np.mean(diffs))
        return (motion_score > MOTION_THRESHOLD), motion_score

    def run_camera(self):
        """カメラ処理メイン"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.config(text="カメラが見つかりません。", fg="red")
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = imutils.resize(frame, width=640)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)

            occlusion_pct = 0.0
            is_live = False

            for (x, y, w, h) in faces:
                occlusion_pct = compute_occlusion_percent(frame, (x, y, w, h))
                live_by_motion, motion_score = self.check_motion(frame)
                is_live = live_by_motion

                color = (0, 255, 0) if is_live else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

                label = f"隠れ率: {occlusion_pct:.1f}%"
                cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            #顔割合_検証用
            if 100 - occlusion_pct < self.min_visible_ratio:
                    self.min_visible_ratio = 100 - occlusion_pct

            # 状態更新
            
            if len(faces) == 0:
                self.status_label.config(text="顔を検出できません", fg="yellow")
                self.occlusion_label.config(text="")
            elif occlusion_pct > OCCLUSION_ALERT:
                
                self.status_label.config(text="顔が隠れています", fg="red")
                self.occlusion_label.config(text=f"見えている割合：約{100 - occlusion_pct:.1f}％\n（最低{self.min_visible_ratio:.1f}％）")
            elif is_live:
                self.status_label.config(text="本人確認：成功（動き検出）", fg="lime")
                self.occlusion_label.config(text=f"顔が{100 - occlusion_pct:.1f}％見えています\n（最低{self.min_visible_ratio:.1f}％）")
            else:
                self.status_label.config(text="本人確認：未完了（動きなし）", fg="orange")
                self.occlusion_label.config(text=f"顔が{100 - occlusion_pct:.1f}％見えています\n（（最低{self.min_visible_ratio:.1f}％）")

            # カメラ映像を別ウィンドウに表示
            cv2.imshow("カメラ映像", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESCキーでも終了
                self.stop_auth()
                break

        self.stop_auth()


# =============================
#  実行部
# =============================
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceAuthApp(root)
    root.geometry("400x300")
    root.mainloop()
