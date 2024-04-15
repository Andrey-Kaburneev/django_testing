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


class CreateNoteTestCase(BaseTestCase):
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
        notes_count_first = Note.objects.count()
        self.client.post(self.url, data=self.form_data)

        notes_count_second = Note.objects.count()

        self.assertEqual(notes_count_first, notes_count_second)

    def test_user_can_create_notes(self):
        notes_count_first = Note.objects.count()

        self.author_client.post(self.url, data=self.form_data)

        notes_count_second = Note.objects.count()
        difference = notes_count_second - notes_count_first
        self.assertEqual(difference, 1)
        note_create = Note.objects.filter(**self.form_data).exists()
        self.assertTrue(note_create)

    def test_not_unique_slug(self):
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
        )
        url = reverse('notes:add')
        notes_count_first = Note.objects.count()

        response = self.author_client.post(url, data={
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        })

        notes_count_second = Note.objects.count()
        difference = notes_count_second - notes_count_first
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(difference, 0)

    def test_auto_generate_slug(self):
        url = reverse('notes:add')
        form_data = {
            'title': 'New Note',
            'slug': 'sl',
            'text': 'text',
        }
        form_data.pop('slug')
        notes_count_first = Note.objects.count()

        response = self.author_client.post(url, data=form_data)

        notes_count_second = Note.objects.count()
        self.assertRedirects(response, reverse('notes:success'))
        difference = notes_count_second - notes_count_first
        self.assertEqual(difference, 1)
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
        notes_count_first = Note.objects.count()

        response = self.author_client.delete(self.delete_url)

        notes_count_second = Note.objects.count()
        self.assertRedirects(response, reverse('notes:success'))
        difference = notes_count_first - notes_count_second
        self.assertEqual(difference, notes_count_first)

    def test_other_user_cant_delete_note(self):
        notes_count_first = Note.objects.count()

        response = self.reader_client.delete(self.delete_url)

        notes_count_second = Note.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(notes_count_first, notes_count_second)

    def test_author_can_edit_note(self):
        form_data = {
            'title': 'title',
            'text': 'text',
            'slug': 'slug',
        }

        response = self.author_client.post(self.edit_url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertTrue(
            Note.objects.filter(author=self.author, **form_data).exists()
        )

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(
            Note.objects.filter(author=self.author, **self.form_data).exists()
        )
