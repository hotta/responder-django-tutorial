"""
urls.py
ルーティング用ファイル
"""
import responder

from auth import is_auth, authorized
import hashlib

from models import User, Question, Choice
import db

api = responder.API()

@api.route('/')
def index(req, resp):
    resp.content = api.template("index.html")

@api.route('/admin')
def admin(req, resp):
    resp.content = api.template("admin.html")

@api.route('/ad_login')
class AdLogin:
    async def on_get(self, req, resp):  # getならリダイレクト
        resp.content = api.template('admin.html')
    
    async def on_post(self, req, resp):
        data = await req.media()
        error_messages = []
    
        if data.get('username') is None or data.get('password') is None:
            error_messages.append('ユーザ名またはパスワードが入力されていません。')
            resp.content = api.template('admin.html', error_messages=error_messages)
            return
    
        username = data.get('username')
        password = hashlib.md5(data.get('password').encode()).hexdigest()
    
        if not is_auth(username, password):
            # 認証失敗
            error_messages.append('ユーザ名かパスワードに誤りがあります。')
            resp.content = api.template('admin.html', error_messages=error_messages)
            return
        
        # 認証成功した場合sessionにユーザを追加しリダイレクト
        resp.set_cookie(key='username', value=username, expires=None, max_age=None)
        api.redirect(resp, '/admin_top')    # ログアウトの場合は expires=0, max_age=0

@api.route('/admin_top')
async def on_session(req, resp):
    """
    管理者ページ
    """

    authorized(req, resp, api)

    # ログインユーザ名を取得
    auth_user = req.cookies.get('username')

    # データベースから質問一覧を選択肢をすべて取得
    questions = db.session.query(Question).all()
    choices = db.session.query(Choice).all()
    db.session.close()

    # 各データを管理者ページに渡す
    resp.content = api.template('administrator.html',
                                auth_user=auth_user,
                                questions=questions,
                                choices=choices)

@api.route('/logout')
async def logout(req, resp):
    # クッキーを削除 - req.cookie → クッキーの中身
    resp.set_cookie(key='username', value='', expires=0, max_age=0)
    api.redirect(resp, '/admin')