import bcrypt
import os
import shutil
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

#やること
#Userテーブル定義に顔写真の保存先パス用のカラムを作る。
#app.pyの登録処理にあるデータベースの追加処理に顔写真を追加する処理を追加する。

# データベースファイル（無ければ自動で作成される）
DATABASE_URL = "sqlite:///users.db"

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# ====== User テーブル定義 ======
class User(Base):
    __tablename__ = "users"  # テーブル名

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    # ファイルパス
    # filepass = Column(String, nullable = True) 
    password_hash = Column(String, nullable=False)


# ====== テーブル作成 ======
Base.metadata.create_all(engine)


# パスワードをハッシュ化して返す
def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()  # DB保存用に文字列化

# 入力されたパスワードとハッシュが一致するかチェック
def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

# 動作確認
pw = "mypassword"
hashed = hash_password(pw)
print(hashed)

# ログイン時
print(check_password("mypassword", hashed))  # → True
print(check_password("wrongpass", hashed))   # → False


# セッション準備
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

def create_user(username: str,password: str ) -> User:
    session = SessionLocal()
    try:
        # ハッシュ化
        ph = hash_password(password)
        user = User(username=username, password_hash=ph)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def authenticate_user(user_id: int, password: str) -> bool:
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False
        return check_password(password, user.password_hash)
    finally:
        session.close()

# 12/05 追加した
def get_user(user_id: int):
    session = SessionLocal()
    try:
        return session.query(User).filter_by(id=user_id).first()
    finally:
        session.close()

# # 12/05 アカウント削除機能
# def delete_user(user_id: int):
#     session = SessionLocal()
#     try:
#         user = session.query(User).filter_by(id=user_id).first()
#         if user:
#             session.delete(user)
#             session.commit()
#     finally:
#         session.close()

def delete_user(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return False
    session.delete(user)
    session.commit()
    session.close()
    return True

def delete_user_picture(user_id):
    path = os.path.join("picture", str(user_id))
    if os.path.exists(path):
        shutil.rmtree(path)

def search_user(user_id):
    users = session.query(User).filter(User.id == user_id).first()
    return users

def get_user_by_name(username: str):
    session = SessionLocal()
    try:
        return session.query(User).filter_by(username=username).first()
    finally:
        session.close()


# 使用例
# u = create_user("sazae", "secret123")
# print("created:", u.id, u.username)

# print("auth correct:", authenticate_user("sazae", "secret123"))  # True
# print("auth wrong:", authenticate_user("sazae", "x"))  # False

# 中身確認

Session = sessionmaker(bind=engine)
session = Session()
def userslist():    
    users = session.query(User).all()

    print("\n===== users テーブルの中身 =====")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Hash: {u.password_hash[:20]}...")