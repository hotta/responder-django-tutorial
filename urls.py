"""
urls.py
ルーティング用ファイル
"""
import responder

from auth import is_auth, authorized
import hashlib

from models import User, Question, Choice
import db

from datetime import datetime

# api = responder.API()

# staticをjinja2で解決するためのstaticフィルターを定義
# def static_filter(path):
#    return '/static/' + path

# jinji2 のフィルターに追加 → AttributeError: 'API' object has no attribute 'jinja_env'
# api.jinja_env.filters['static'] = static_filter

# 「jinja2のグローバル変数を使う方法も動かない
# api.jinja_env.globals ...

# static_dir も効いていない気がする？( 'style.cc' だけだと 404 になる)
# api = responder.API(static_dir='static')
api = responder.API()

@api.route('/')
class Index:
    def on_get(self, req, resp):

        # 最新５個の質問を降順で取得
        questions = self.get_queryset()

        # 最新かどうか
        emphasized = [question.was_published_recently() for question in questions]

        # フォーマットを変更して必要なものだけ
        pub_date = [q.pub_date.strftime('%Y-%m-%d %H:%M:%S') for q in questions]

        resp.content = api.template("index.html", questions=questions, emphasized=emphasized, pub_date=pub_date)

    def get_queryset(self, latest=5):
        """
        最新latest個の質問を返す
        :param latest:
        :return
        """
        # 公開日の降順でソートして取得
        # filter()で現在日時より小さいものだけを取得する
        questions = db.session.query(Question).\
            filter(Question.pub_date <= datetime.now()).\
            order_by(Question.pub_date.desc()).all()
        db.session.close()

        return questions[:latest]

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

    # 直近の投稿かどうか
    was_recently = [q.was_published_recently() for q in questions]

    # 各データを管理者ページに渡す
    resp.content = api.template('administrator.html',
                                auth_user=auth_user,
                                questions=questions,
                                choices=choices,
                                was_recently=was_recently
                                )

@api.route('/logout')
async def logout(req, resp):
    # クッキーを削除 - req.cookie → クッキーの中身
    resp.set_cookie(key='username', value='', expires=0, max_age=0)
    api.redirect(resp, '/admin')


@api.route('/add_Question')
class AddQuestion:
    async def on_get(self, req, resp):
        """
        getの場合は追加専用ページを表示する
        """
        authorized(req, resp, api)
        date = datetime.now()

        resp.content = api.template('add_question.html', date=date)
        
    async def on_post(self, req, resp):
        """
        postの場合は受け取ったデータをQuestionテーブルに追加する。
        """
        data = await req.media()
        error_messages = list()

        if data.get('question_text') is None:
            error_messages.append('質問内容が入力されていません。')

        if data.get('date') is None or data.get('time') is None:
            error_messages.append('公開日時が入力されていません。')

        # 配列として受け取ったフォームはget_list()で取り出す
        choices = data.get_list('choices[]')
        votes = data.get_list('votes[]')

        if len(choices) == 0 or len(votes) == 0 or len(choices) != len(votes):
            error_messages.append('選択肢内容に未入力の項目があります。')

        if len(choices) < 1:
            error_messages.append('選択肢は２つ以上必要です。')

        # 何かしらエラーがあればリダイレクト
        if len(error_messages) != 0:
            resp.content = api.template('add_question.html', error_messages=error_messages,
                                        date=datetime.now())
            return

        # テーブルにQuestionを追加
        date = [int(d) for d in data.get('date').split('-')]
        time = [int(d) for d in data.get('time').split(':')]

        question = Question(data.get('question_text'),
                            datetime(date[0], date[1], date[2],
                                    time[0], time[1], time[2]))
        db.session.add(question)
        db.session.commit()

        """ テーブルにChoicesを追加 """
        foreign_key = question.id
        q_choices = list()

        for i, choice in enumerate(choices):
            q_choices.append(Choice(foreign_key, choice, int(votes[1])))

        db.session.add_all(q_choices)
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

@api.route('/change/{table_name}/{data_id}')
class ChangeData:
    async def on_get(self, req, resp, table_name, data_id):
        authorized(req, resp, api)

        table = Question if table_name == 'question' else Choice
        # [table].id == data_idとなるようなレコードをひとつ持ってくる
        field = db.session.query(table).filter(table.id == data_id).first()
        resp.content = api.template('/change.html', field=field, table_name=table_name)

    async def on_post(self, req, resp, table_name, data_id):
        data = await req.media()
        error_messages = list()

        # 何も入力されていない場合
        text = table_name + '_text'
        if data.get(text) is None:
            error_messages.append('入力されていない項目があります。')
            resp.content = api.template('change.html', error_messages=error_messages,
                                        field=data, table_name=table_name)
            return

        # データ更新
        table = Question if table_name == 'question' else Choice
        record = db.session.query(table).filter(table.id == data_id).first()

        if table is Question:
            record.question_text = data.get(text)
            record.pub_date = datetime(
                int(data['year']),
                int(data['month']),
                int(data['day']),
                int(data['hour']),
                int(data['minute']),
                int(data['second'])
            )
        else:
            record.choice_text = data.get(text)

        db.session.commit()
        db.session.close()

        api.redirect(resp, '/admin_top')

@api.route('/delete/{table_name}/{data_id}')
class DeleteData:
    async def on_get(self, req, resp, table_name, data_id):
        authorized(req, resp, api)

        table = Question if table_name == 'question' else Choice
        # table.id == data_idとなるようなレコードをひとつ持ってくる
        field = db.session.query(table).filter(table.id == data_id).first()
        db.session.commit()
#        db.session.close()     # これを書くと以下のエラーで落ちる
# sqlalchemy.orm.exc.DetachedInstanceError: Instance <Choice at 0x1e94667b6c8> 
# is not bound to a Session; attribute refresh operation cannot proceed 
# (Background on this error at: http://sqlalche.me/e/bhk3)

        resp.content = api.template('/delete.html', field=field, table_name=table_name)
        db.session.close()  # ここに書くのが正しいらしい

    async def on_post(self, req, resp, table_name, data_id):
        data = await req.media()

        # データ削除
        table = Question if table_name == 'question' else Choice
        record = db.session.query(table).filter(table.id == data_id).first()
        db.session.delete(record)

        # 紐付いた質問も削除
        if table is Question:
            choices = db.session.query(Choice).filter(Choice.question == data_id).all()
            for choice in choices:
                db.session.delete(choice)

        db.session.commit()
        db.session.close()

        api.redirect(resp, '/admin_top')

@api.route('/detail/{q_id}')
class Detail:
    async def on_get(self, req, resp, q_id):
        question = db.session.query(Question).filter(Question.id == q_id).first()
        choices = db.session.query(Choice).filter(Choice.question == q_id).all()
        db.session.close()

        if question.pub_date > datetime.now():
            # 404 のハンドリングは responder 自体にパッチを当てないと動かない
            # resp.content = self.template('404.html')
            resp.content = api.redirect(resp, '/')

        resp.content = api.template('detail.html', question=question, choices=choices)

@api.route('/vote/{q_id}')
class Vote:
    async def on_post(self, req, resp, q_id):
        # postデータを取得
        data = await req.media()

        # 該当するchoiceを取得しvoteをインクリメント
        choice = db.session.query(Choice).filter(Choice.id == data.get('choice')).first()
        choice.votes += 1
        db.session.commit()
        db.session.close()

        # リダイレクト
        url_redirect = '/result/' + str(q_id)
        api.redirect(resp, url_redirect)

@api.route('/result/{q_id}')
class Result:
    async def on_get(self, req, resp, q_id):

        question = db.session.query(Question).filter(Question.id == q_id).first()
        choices = db.session.query(Choice).filter(Choice.question == q_id).all()
        db.session.close()

        resp.content = api.template('result.html', question=question, choices=choices)
