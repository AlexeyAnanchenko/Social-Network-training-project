from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='FirstName')
        cls.user_2 = User.objects.create_user(username='SecondName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        # Создаём 11 постов с первыми группой и пользователем
        for post in range(1, 12):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовая запись {post}',
                group=cls.group,
            )
        # Создадим ещё один пост без группы
        Post.objects.create(author=cls.user_2, text='Тестовая запись 12')
        # Создаём ещё 2 поста со вторыми группой и пользователем
        for post in range(13, 15):
            Post.objects.create(
                author=cls.user_2,
                text=f'Тестовая запись {post}',
                group=cls.group_2,
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.posts_obj = list(Post.objects.all())

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'FirstName'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html'
        }
        # Проверяем, что при обращении к name вызывается соответствующий
        # HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_pages_with_posts_show_correct_context(self):
        """Шаблоны с функцией выгрузки постов сформированы с правильным
        контекстом
        """
        # Набор для проверки index.html (все созданные посты)
        set_compare_1 = {
            'username': 'SecondName',
            'text': 'Тестовая запись 14',
            'group': 'Тестовая группа 2',
            'posts_count': 14
        }
        # Набор для проверки group_list, profile (посты с определённой группой
        # или автором)
        set_compare_2 = {
            'username': 'FirstName',
            'text': 'Тестовая запись 11',
            'group': 'Тестовая группа',
            'posts_count': 11
        }
        reverse_name_sorting = {
            reverse('posts:index'): set_compare_1,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                set_compare_2,
            reverse('posts:profile', kwargs={'username': 'FirstName'}):
                set_compare_2
        }
        for reverse_name, sorting in reverse_name_sorting.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                # Взяли первый элемент из отфильтрованного списка объектов
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                post_pub_date_0 = first_object.pub_date
                # Посчитаем общее кол-во постов исходя из текущей итерации
                count_obj = response.context['paginator'].count
                # Проверяем, что содержание первого объекта совпадает с
                # последним созданным постом
                self.assertEqual(post_author_0, sorting['username'])
                self.assertEqual(post_text_0, sorting['text'])
                self.assertEqual(post_group_0, sorting['group'])
                self.assertEqual(
                    post_pub_date_0,
                    self.posts_obj[14 - sorting['posts_count']].pub_date
                )
                # Проверяем общее кол-во постов по фильтрации
                self.assertEqual(count_obj, sorting['posts_count'])
                # Проверяем дополнительные значения в словаре контекста
                if 'group' in response.context.keys():
                    self.assertEqual(
                        response.context['group'],
                        PostPagesTests.group
                    )
                if 'author' in response.context.keys():
                    self.assertEqual(
                        response.context['author'],
                        PostPagesTests.user
                    )

    def test_posts_paginator_first_page(self):
        """Проверяем Паджинатор, первую страницу"""
        reverse_name_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'FirstName'})
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.NUM_POSTS
                )

    def test_posts__paginator_second_page(self):
        """Проверяем Паджинатор, вторую страницу"""
        reverse_name_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'FirstName'})
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    response.context['paginator'].count - settings.NUM_POSTS
                )

    def test_posts_post_detail_show_correct_context(self):
        """Проверяем, что шаблон post_detail сформирован с правильным
        контекстом
        """
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        post = response.context['post']
        post_author = post.author.username
        post_text = post.text
        post_group = post.group.title
        post_pub_date = post.pub_date
        self.assertEqual(post_author, 'FirstName')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(post_text, 'Тестовая запись 1')
        self.assertEqual(
            post_pub_date,
            self.posts_obj[13].pub_date
        )
        self.assertEqual(response.context['post_count'], 11)

    def test_posts_create_and_edit_post_show_correct_context(self):
        """Шаблон create_post и post_edit сформированы с правильным
        контекстом.
        """
        reverse_name_list = [
            reverse('posts:create_post'),
            reverse('posts:post_edit', kwargs={'post_id': 1})
        ]
        for reverse_name in reverse_name_list:
            response = self.authorized_client.get(reverse_name)
            if 'is_edit' in response.context.keys():
                self.assertEqual(response.context['is_edit'], True)
                self.assertEqual(response.context['post'], self.posts_obj[13])
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_posts_group_assign_and_present_pages(self):
        """Доп. проверка присутствия поста с группой на нужных страницах"""
        reverse_name_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'FirstName'})
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                # 6-й созданный пост будет присутствовать на всех первых стр.
                self.assertIn(self.posts_obj[5], response.context['page_obj'])

    def test_posts_group_assign_and_not_present_pages(self):
        """Проверка отсутствия поста с группой на не нужных страницах"""
        reverse_name_list = [
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'}),
            reverse('posts:profile', kwargs={'username': 'SecondName'})
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertNotIn(
                    self.posts_obj[13],
                    response.context['page_obj']
                )

    def test_posts_group_not_assign(self):
        """Проверка поста без группа: должен выгружаться только в index"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(self.posts_obj[2], response.context['page_obj'])
        # А теперь проверим, что не отображается на страницах групп и FirstUser
        reverse_name_list = [
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'FirstName'}),
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'}),
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertNotIn(
                    self.posts_obj[2],
                    response.context['page_obj']
                )
