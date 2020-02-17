"""
models.py
モデルの定義
"""
import os
from datetime import datetime

from db import Base
from db import engine

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.dialects.mysql import INTEGER

import hashlib

SQLITE3_NAME = "./db.sqlite3"   # db.py の RDB_PATH との２重管理


class Question(Base):
    """
    Questionテーブル

    id              :   主キー
    question_text   :   質問事項
    pub_date        :   公開日
    """
    __tablename__ = 'question'

    id = Column(
        'id',
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )
    question_text = Column('question_text', String(256))
    pub_date = Column(
        'pub_date',
        DateTime,
        default=datetime.now(),
        nullable=False,
        server_default=current_timestamp()
    )

    def __init__(self, question_text, pub_date=datetime.now()):
        self.question_text = question_text
        self.pub_date = pub_date

    def __str__(self):  # オブジェクトの文字列を返す
        return str(self.id) + ':' + self.question_text + '-' \
             + self.pub_date.strftime('%Y/%m/%d - %H:%M:%S')

class Choice(Base):
    """
    Choiceテーブル

    id          :   主キー
    question    :   紐付けられた質問（外部キー）
    choice_text :   選択肢のテキスト
    votes       :   投票数
    """
    __tablename__ = 'choice'
    id = Column(
        'id',
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )
    question = Column('question', ForeignKey('question.id'))
    choice_text = Column('choice_text', String(256))
    votes = Column('votes', INTEGER(unsigned=True), nullable=False)

    def __init__(self, question, choice_text, vote=0):
        self.question = question
        self.choice_text = choice_text
        self.votes = vote

    def __str__(self):  # オブジェクトの文字列を返す
        return str(self.id) + ':' + self.choice_text + '-' + self.votes

class User(Base):
    """
    Userテーブル

    id          :   主キー
    username    :   ユーザ名
    password    :   パスワード
    """
    __tablename__ = 'user'
    id = Column(
        'id',
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )
    username = Column('username', ForeignKey('question.id'))
    password = Column('password', String(256))

    def __init__(self, username, password):
        self.username = username
        # パスワードはハッシュ化して保存
        self.password = hashlib.md5(password.encode()).hexdigest()

    def __str__(self):  # オブジェクトの文字列を返す
        return str(self.id) + ':' + self.username
    


if __name__ == "__main__":
    path = SQLITE3_NAME
    if not os.path.isfile(path):

        # テーブルを作成する
        Base.metadata.create_all(engine)
