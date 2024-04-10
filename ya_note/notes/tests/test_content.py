from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


from notes.models import Note

from django.contrib.auth import get_user_model


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.user)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    def test_note_not_in_list_for_another_user(self):
        """Заметка не доступна другому пользователю"""
        url = reverse('notes:list')
        response = self.reader_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.note, response.context['object_list'])

    def test_note_list_view(self):
        """Список заметок"""
        url = reverse('notes:list')
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.note, response.context['object_list'])

    def test_create_note_page_contains_form(self):
        """Страница создания заметки содержит форму"""
        url = reverse('notes:add')
        response = self.auth_client.get(url)
        self.assertIn('form', response.context)

    def test_edit_note_page_contains_form(self):
        """Страница редактирование содержит форму"""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.get(url)
        self.assertIn('form', response.context)
