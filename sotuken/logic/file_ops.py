import os
import shutil

def move_upload_temp_to_user(user_id):
    # 移動元（upload_temp）
    src_dir = "upload_temp"

    # 移動先（picture/<user_id>）
    dst_dir = os.path.join("picture", str(user_id))

    # 念のため存在チェックだけ行う（作成はしない）
    if not os.path.isdir(dst_dir):
        raise RuntimeError(f"Destination directory does not exist: {dst_dir}")

    # upload_temp 内のファイルを走査
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)

        # ファイルのみ対象
        if not os.path.isfile(src):
            continue

        dst = os.path.join(dst_dir, name)

        # 同名ファイルがあればエラー
        if os.path.exists(dst):
            raise RuntimeError(f"Already exists: {dst}")

        # ファイル移動
        shutil.move(src, dst)
