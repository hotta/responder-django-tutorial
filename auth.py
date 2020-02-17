"""
auth.py
認証系の関数群
"""
from models import User
import db


def is_auth(username, password):
    """
    Userテーブルに存在するか否かを返す
    """
    users = db.session.query(User.username, User.password)
    db.session.close()

    for user in users:
        if user.username == username and user.password == password:
            return True
    return False


def authorized(req, resp, api):
    """
    cookieにusernameが存在しない場合にログインページにリダイレクトする
    （ログインしていない場合）
    """
    if 'username' not in req.cookies:
        api.redirect(resp, '/admin')