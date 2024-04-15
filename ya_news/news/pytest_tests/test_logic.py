from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from conftest import TEXT_COMMENT
from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, new_text_comment, news):
    """Создание комментария анонимом"""
    url = reverse('news:detail', args=(news.id,))
    start_comment_count = Comment.objects.count()

    client.post(url, data=new_text_comment)

    final_comment_count = Comment.objects.count()
    assert final_comment_count == start_comment_count


def test_user_can_create_comment(
        author_client, author, new_text_comment, news):
    """Создание комментария пользователем"""
    url = reverse('news:detail', args=(news.id,))
    comments_count_first = Comment.objects.count()

    author_client.post(url, data=new_text_comment)

    comments_count_second = Comment.objects.count()
    assert comments_count_second - comments_count_first == 1
    assert Comment.objects.filter(
        text=new_text_comment['text'], news=news, author=author
    ).exists()


def test_user_cant_use_bad_words(author_client, news):
    """Использование запрещенных слов"""
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=(news.id,))
    comments_count_first = Comment.objects.count()

    response = author_client.post(url, data=bad_words_data)

    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count_second = Comment.objects.count()
    assert comments_count_first - comments_count_second == 0


def test_author_can_delete_comment(author_client, news, comment):
    """Доступ автора к удалению комментария"""
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = reverse('news:delete', args=(comment.id,))
    comments_count_first = Comment.objects.count()

    response = author_client.delete(url_to_comments)

    assertRedirects(response, news_url + '#comments')
    comments_count_second = Comment.objects.count()
    assert comments_count_first - comments_count_second == 1


def test_user_cant_delete_comment_of_another_user(
        admin_client, comment
):
    """Доступ пользователя к удалению комментария"""
    comment_url = reverse('news:delete', args=(comment.id,))
    comments_count_first = Comment.objects.count()

    response = admin_client.delete(comment_url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count_second = Comment.objects.count()
    assert comments_count_first == comments_count_second


def test_author_can_edit_comment(
        author_client, new_text_comment, news, comment):
    """Доступ автора к редактированию комментария"""
    news_url = reverse('news:detail', args=(news.id,))
    comment_url = reverse('news:edit', args=(comment.id,))

    response = author_client.post(comment_url, data=new_text_comment)

    assertRedirects(response, news_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == new_text_comment['text']


def test_user_cant_edit_comment_of_another_user(
        admin_client, new_text_comment, comment):
    """Доступность пользователю редактирования чужого комментария"""
    comment_url = reverse('news:edit', args=(comment.id,))

    response = admin_client.post(comment_url, data=new_text_comment)

    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == TEXT_COMMENT
