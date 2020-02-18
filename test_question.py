"""
test_question.py
サンプルテストケース  # pytest -p no:warings で pytest 自体の警告を抑止できる
"""
import pytest
import run as myApp

from datetime import datetime, timedelta

from models import Question

@pytest.fixture
def api():
    return myApp.api

class TestQuestionModel:
    def test_was_published_recently_with_future_question(self, api):
        """
        未来の質問に対してwas_published_recently()はFalseを返す
        :param api:
        :return:
        """
        # 未来の公開日となる質問の作成
        time = datetime.now() + timedelta(days=30)
        feature_question = Question('future_question', pub_date=time)

        # これはFalseとなるはず
        assert feature_question.was_published_recently() is False

    def test_was_published_recently_with_boundary_question(self, api):
        """
        === 境界値テスト ===
        １日１秒前の質問に対しては、was_published_recently()はFalseを返すはず
        23時間59分59秒以内であれば、was_published_recently()はTrueを返すはず
        """
        # 最近の境界値となる質問を作成
        # was_published_recently() は <= で聞いているので、１秒足さないとテストに通らない
        time_old = datetime.now() - timedelta(days=1, seconds=1)
        time_rec = datetime.now() - timedelta(hours=23, minutes=59, seconds=59)
        old_question = Question('old_question', time_old)
        rec_question = Question('recent_question', time_rec)

        assert old_question.was_published_recently() is False
        assert rec_question.was_published_recently() is True