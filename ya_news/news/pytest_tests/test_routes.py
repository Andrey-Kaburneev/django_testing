from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects
from django.urls import reverse


@pytest.mark.django_db  # Arrange
@pytest.mark.parametrize(
    'name',
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_pages_availability(client, name):
    """Проверяем доступность страниц анониму"""
    url = reverse(name)

    response = client.get(url)  # Act

    assert response.status_code == HTTPStatus.OK  # Assert


@pytest.mark.django_db  # Arrange
def test_detail_page(client, news):
    """Страница отдельной записи"""
    url = reverse('news:detail', args=(news.id,))

    response = client.get(url)  # Act

    assert response.status_code == HTTPStatus.OK  # Assert


@pytest.mark.parametrize(  # Arrange
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_availability_for_comment_edit_and_delete(
        parametrized_client, expected_status, name, comment
):
    """Доступность удаления и редактирования комментария"""
    url = reverse(name, args=(comment.id,))

    response = parametrized_client.get(url)  # Act

    assert response.status_code == expected_status  # Assert


@pytest.mark.django_db  # Arrange
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_redirect_for_anonymous_client(client, name, comment):
    """Перенаправляем анонима на строницу логина"""
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.id,))
    expected_url = f'{login_url}?next={url}'

    response = client.get(url)  # Act

    assertRedirects(response, expected_url)  # Assert
