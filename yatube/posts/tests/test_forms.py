from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostCreateFormTests(TestCase):

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='Name',)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        tasks_count = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Name'})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='Тестовый текст',).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        Post.objects.create(author=self.user, text='Тестовая запись')
        form_data = {
            'author': self.user,
            'text': 'Поменяли запись',
        }
        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.get(pk=1).text, 'Поменяли запись')
