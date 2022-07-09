import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='Name',)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовая запись'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        created_post = Post.objects.get(pk=posts_count + 1)
        self.assertEqual(form_data['author'], created_post.author)
        self.assertEqual(form_data['text'], created_post.text)
        self.assertEqual(form_data['group'], created_post.group.id)
        self.assertEqual(f'posts/{uploaded.name}', created_post.image)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'post_id': self.post.id,
            'author': self.user,
            'text': 'Поменяли запись',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': form_data['post_id']}),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.get(pk=form_data['post_id']).text,
            'Поменяли запись'
        )

    def test_not_create_post(self):
        """Не авторизованный пользователь не может создать запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
        }
        response = self.guest_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('posts:create_post')}"
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        created_comment = Comment.objects.get(pk=comment_count + 1)
        self.assertEqual(form_data['text'], created_comment.text)
        self.assertEqual(self.post, created_comment.post)
        self.assertEqual(self.user, created_comment.author)

    def test_not_create_comment(self):
        """Не авторизованный пользователь не может создать запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next="
            f"{reverse('posts:add_comment', kwargs={'post_id': self.post.id})}"
        )
        self.assertEqual(Comment.objects.count(), comments_count)
