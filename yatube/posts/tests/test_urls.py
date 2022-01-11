from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='FirstUser')
        cls.second_user = User.objects.create_user(username='TwoUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем первый клиент для авторизации
        self.authorized_client = Client()
        # Создаем второй клиент для авторизации
        self.second_authorized_client = Client()
        # Авторизуем первого пользователя
        self.authorized_client.force_login(PostsUrlTests.user)
        # Авторизуем второго пользователя
        self.second_authorized_client.force_login(PostsUrlTests.second_user)

    def test_posts_url_unauthorized_client(self):
        """Проверяем список страниц доступных для неавторизованных клиентов"""
        public_url = [
            '/',
            '/group/test-slug/',
            '/profile/FirstUser/',
            f'/posts/{PostsUrlTests.post.id}/'
        ]
        for url in public_url:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_posts_url_authorized_client(self):
        """Проверка доступности страниц для авторизованных пользователей"""
        non_public_url = [
            '/create/',
            f'/posts/{PostsUrlTests.post.id}/edit/'  # доступно только автору
        ]
        for url in non_public_url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_posts_url_redirect_unauthorized_client(self):
        """Проверяем перенаправление анонимного
        пользователя на страницу логина
        """
        non_public_url = [
            '/create/',
            f'/posts/{PostsUrlTests.post.id}/edit/'  # доступно только автору
        ]
        for url in non_public_url:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_posts_url_redirect_authorized_client(self):
        """Проверяем перенаправление авторизованного пользователя
        со страницы редактирования поста на страницу просмотра"""
        response = self.second_authorized_client.get(
            f'/posts/{PostsUrlTests.post.id}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{PostsUrlTests.post.id}/')

    def test_posts_url_unexisting_page(self):
        """Проверяем статус при обращении к несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_posts_template(self):
        """Проверка соответствия URL-адреса и шаблона"""
        url_template = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/FirstUser/': 'posts/profile.html',
            f'/posts/{PostsUrlTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostsUrlTests.post.id}/edit/': 'posts/create_post.html'
        }
        for url, template in url_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)