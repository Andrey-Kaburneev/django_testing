from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.test.client import Client

import pytest

from news.models import News, Comment

TEXT_COMMENT = 'Текст комментария'


@pytest.fixture
def new_text_comment():
    """Новый текст комментария"""
    return {'text': 'Новый текст'}


@pytest.fixture
def author(django_user_model):
    """Создаем автор"""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    """Создаем не автора"""
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author, client):
    """Клиент автора"""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    """Клиент не автора"""
    client = Client()
    client.force_login(not_author)  # Логиним обычного пользователя в клиенте.
    return client


@pytest.fixture
def news():
    """Создаем новость"""
    news = News.objects.create(
        title='Заголовок',
        text='Текст новости',
        date=datetime.today(),
    )
    return news


@pytest.fixture
def comment(news, author):
    """Создаем комент"""
    comment = Comment.objects.create(
        text=TEXT_COMMENT,
        news=news,
        author=author
    )
    return comment


@pytest.fixture
def list_news():
    """Список новостей"""
    today, list_news = datetime.today(), []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        news = News.objects.create(
            title='Новость {index}',
            text='Текст новости',
        )
        news.date = today - timedelta(days=index)
        news.save()
        list_news.append(news)
    return list_news


@pytest.fixture
def list_comments(news, author):
    """Список комментариев"""
    now, list_comment = timezone.now(), []
    for index in range(2):
        comment = Comment.objects.create(
            text='Текст {index}',
            news=news,
            author=author,
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        list_comment.append(comment)
