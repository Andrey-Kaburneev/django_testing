from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.template.defaultfilters import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class BaseTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор записи')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)


class TestNoteCreation(BaseTestCase):
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.anonymous = User.objects.create(username='Аноним')
        cls.url = reverse('notes:add')
        cls.form_data = {'text': cls.NOTE_TEXT,
                         'slug': 'slug',
                         'title': 'title'}

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_notes(self):
        self.author_client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_not_unique_slug(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:add')
        response = self.author_client.post(url, data={
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        })
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_auto_generate_slug(self):
        url = reverse('notes:add')
        form_data = {
            'title': 'New Note',
            'slug': 'sl',
            'text': 'text',
        }
        form_data.pop('slug')
        response = self.author_client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(BaseTestCase):
    COMMENT_TEXT = 'Запись'
    NEW_COMMENT_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', slug='slug', author=cls.author
        )
        note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.url_to_note = note_url
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        response = self.reader_client.delete(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_author_can_edit_note(self):
        form_data = {
            'title': 'title',
            'text': 'text',
            'slug': 'slug',
        }
        response = self.author_client.post(self.edit_url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, form_data['title'])
        self.assertEqual(self.note.text, form_data['text'])
        self.assertEqual(self.note.slug, form_data['slug'])

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        note_from_db = Note.objects.get(slug=self.note.slug)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
