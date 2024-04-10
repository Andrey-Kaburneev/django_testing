from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from notes.models import Note

from django.contrib.auth import get_user_model

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.user = User.objects.create(username='testUser')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)

# Страницы доступные анониму
    def test_pages_availability(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


# Страницы редактирования,удаления и отдельной записи доступны только автору
    def test_availability_for_note_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

# Доступ к записи для автора
    def test_detail_note_for_author(self):
        url = reverse('notes:detail', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

# Доступ к записи для анонима
    def test_detail_note_for_not_the_author(self):
        url = reverse('notes:detail', args=(self.note.slug,))
        self.client.force_login(self.reader)
        response = self.client.get(url) 
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

# Может ли авторизованный пользователь зайти на страницы
    def test_pages_availability_for_authorized(self):
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
        )
        self.client.force_login(self.reader)
        for name, args in urls:
            with self.subTest(user=self.reader, name=name):
                url = reverse(name, args=args,)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

# Редирект анониман на страницу логина
    def test_pages_availability_for_authorized_login(self):
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,))
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                redirect_url = f'{login_url}?next={url}'
                self.assertRedirects(response, redirect_url)
