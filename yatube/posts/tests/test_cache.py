from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostsCacheTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='User')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        self.guest_client = Client()

    def test_cache_index(self):
        """Проверяем корректность работы кэша в шаблоне index.html"""
        response = self.guest_client.get(reverse('posts:index'))
        # проверим, что получили ответ
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # проверим наличие созданного поста в контенте ответа
        self.assertIn(self.post.text, response.content.decode())
        # удалим пост
        self.post.delete()
        # сделаем повторный get запрос
        response = self.guest_client.get(reverse('posts:index'))
        # проверяем, что в кешэ пост сохранился
        self.assertIn(self.post.text, response.content.decode())
        # Очищаем кеш
        cache.clear()
        # делаем ещё один запрос
        response = self.guest_client.get(reverse('posts:index'))
        # Провеяем, что поста уже нет в HttpResponse
        self.assertNotIn(self.post.text, response.content.decode())
