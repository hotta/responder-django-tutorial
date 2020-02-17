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

@api.route('/add_Question')
class addQuestion:
    async def on_get(self, req, resp):
        """
        getの場合は追加専用ページを表示させる。
        """
        authorized(req, resp, api)

        resp.content = api.template('add_question.html')

    async def on_post(self, req, resp):
        """
        postの場合は受け取ったデータをQuestionテーブルに追加する。
        """
        data = await req.media()
        error_messages = list()

        # 何も入力されていない場合
        if data.get('question_text') is None:
            error_messages.append('質問内容が入力されていません。')
            resp.content = api.template('add_question.html', error_messages=error_messages)
            return

        # テーブルに追加
        question = Question(data.get('question_text'))
        db.session.add(question)
        db.session.commit()
        db.session.close()

        api.redirect(resp, '/admin_top')

@api.route('/add_Choice')
class AddChoice:
    async def on_get(self, req, resp):
        """
        getの場合は追加専用ページを表示させる。
        """
        authorized(req, resp, api)

        questions = db.session.query(Question.id, Question.question_text)
        resp.content = api.template('add_choice.html', questions=questions)

    async def on_post(self, req, resp):
        """
        postの場合は受け取ったデータをChoiceテーブルに追加する。
        """
        data = await req.media()
        error_messages = list()

        # 何も入力されていない場合
        if data.get('choice_text') is None:
            error_messages.append('選択肢が入力されていません。')
            questions = db.session.query(Question.id, Question.question_text)
            resp.content = api.template('add_choice.html', error_messages=error_messages, questions=questions)
            return

        # テーブルに追加
        choice = Choice(data.get('question'), data.get('choice_text'))
        db.session.add(choice)
        db.session.commit()
        db.session.close()

        api.redirect(resp, '/admin_top')