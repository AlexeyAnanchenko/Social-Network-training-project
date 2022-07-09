import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.obj = []
        cls.user_group_1 = range(1, 12)
        cls.user_2_not_group = 12
        cls.user_group_2 = range(13, 15)
        for i in cls.user_group_1:
            cls.obj.append(Post(
                id=i,
                author=cls.user,
                text=f'Тестовая запись {i}',
                group=cls.group,
                image=cls.uploaded,
            ))
        cls.obj.append(Post(
            id=cls.user_2_not_group,
            author=cls.user_2,
            text=f'Тестовая запись {cls.user_2_not_group}'
        ))
        for i in cls.user_group_2:
            cls.obj.append(Post(
                id=i,
                author=cls.user_2,
                text=f'Тестовая запись {i}',
                group=cls.group_2,
                image=cls.uploaded,
            ))
        Post.objects.bulk_create(cls.obj)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.authorized_client_2.force_login(PostPagesTests.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ):
                'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            ):
                'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': len(PostPagesTests.obj)}
            ):
                'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': len(PostPagesTests.user_group_1)}
            ):
                'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_show_correct_context(self):
        """Проверяем, что шаблон index сформирован с правильным
        контекстом
        """
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author.username
        post_text = first_object.text
        post_group = first_object.group.title
        post_pub_date = first_object.pub_date
        post_image = first_object.image
        count_obj = response.context['paginator'].count
        self.assertEqual(post_author, PostPagesTests.user_2.username)
        self.assertEqual(
            post_text,
            PostPagesTests.obj[len(PostPagesTests.obj) - 1].text
        )
        self.assertEqual(post_group, PostPagesTests.group_2.title)
        self.assertEqual(
            post_pub_date,
            PostPagesTests.obj[len(PostPagesTests.obj) - 1].pub_date
        )
        self.assertIn(list(post_image)[0], PostPagesTests.small_gif)
        self.assertEqual(count_obj, len(PostPagesTests.obj))

    def test_posts_group_list_and_profile_show_correct_context(self):
        """Проверяем, что шаблон group_post и profile сформирован с правильным
        контекстом
        """
        reverse_name = [
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
        ]
        for name in reverse_name:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                first_object = response.context['page_obj'][0]
                post_author = first_object.author.username
                post_text = first_object.text
                post_group = first_object.group.title
                post_pub_date = first_object.pub_date
                post_image = first_object.image
                count_obj = response.context['paginator'].count
                self.assertEqual(post_author, PostPagesTests.user.username)
                self.assertEqual(
                    post_text,
                    PostPagesTests.obj[
                        len(PostPagesTests.user_group_1) - 1
                    ].text
                )
                self.assertEqual(post_group, PostPagesTests.group.title)
                self.assertEqual(
                    post_pub_date,
                    PostPagesTests.obj[
                        len(PostPagesTests.user_group_1) - 1
                    ].pub_date
                )
                self.assertIn(list(post_image)[0], PostPagesTests.small_gif)
                self.assertEqual(count_obj, len(PostPagesTests.user_group_1))
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
                if 'following' in response.context.keys():
                    self.assertEqual(
                        response.context['following'],
                        PostPagesTests.follow
                    )

    def test_posts_paginator_first_page(self):
        """Проверяем Паджинатор, первую страницу"""
        reverse_name_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
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
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
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
        num_post = len(PostPagesTests.obj)
        comment = Comment.objects.create(
            post=PostPagesTests.obj[num_post - 1],
            text='Текст комментария',
            author=PostPagesTests.user
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': num_post})
        )
        post = response.context['post']
        post_author = post.author.username
        post_text = post.text
        post_group = post.group.title
        post_pub_date = post.pub_date
        post_image = post.image
        self.assertEqual(post_author, PostPagesTests.user_2.username)
        self.assertEqual(post_group, PostPagesTests.group_2.title)
        self.assertEqual(post_text, PostPagesTests.obj[num_post - 1].text)
        self.assertEqual(
            post_pub_date,
            PostPagesTests.obj[num_post - 1].pub_date
        )
        self.assertIn(list(post_image)[0], PostPagesTests.small_gif)
        self.assertIn(comment, response.context['comments'])
        self.assertEqual(
            response.context['post_count'],
            (len(PostPagesTests.user_group_2) + 1)
        )

    def test_posts_create_and_edit_post_show_correct_context(self):
        """Шаблон create_post и post_edit сформированы с правильным
        контекстом.
        """
        num_post = PostPagesTests.user_group_1[0]
        reverse_name_list = [
            reverse('posts:create_post'),
            reverse('posts:post_edit', kwargs={'post_id': num_post})
        ]
        for reverse_name in reverse_name_list:
            response = self.authorized_client.get(reverse_name)
            if 'is_edit' in response.context.keys():
                self.assertEqual(response.context['is_edit'], True)
                self.assertEqual(
                    response.context['post'],
                    PostPagesTests.obj[num_post - 1]
                )
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
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertIn(
                    PostPagesTests.obj[len(PostPagesTests.user_group_1) - 1],
                    response.context['page_obj']
                )

    def test_posts_group_assign_and_not_present_pages(self):
        """Проверка отсутствия поста с группой на не нужных страницах"""
        reverse_name_list = [
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group_2.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user_2.username}
            )
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertNotIn(
                    PostPagesTests.obj[PostPagesTests.user_group_1[0]],
                    response.context['page_obj']
                )

    def test_posts_group_not_assign(self):
        """Проверка поста без группы: должен выгружаться только в index"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(
            PostPagesTests.obj[PostPagesTests.user_2_not_group - 1],
            response.context['page_obj']
        )
        reverse_name_list = [
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group_2.slug}
            ),
        ]
        for reverse_name in reverse_name_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertNotIn(
                    PostPagesTests.obj[PostPagesTests.user_2_not_group - 1],
                    response.context['page_obj']
                )

    def test_posts_user_can_unfollow(self):
        """Авторизованный пользователь может отменить подписку на автора"""
        follow = Follow.objects.create(
            user=PostPagesTests.user_2,
            author=PostPagesTests.user,
        )
        self.authorized_client_2.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTests.user.username}
        ))
        self.assertNotIn(
            follow,
            PostPagesTests.user_2.follower.all()
        )

    def test_posts_user_can_follow(self):
        """Авторизованный пользователь может подписаться на другого автора"""
        follow_count = PostPagesTests.user.follower.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user_2.username}
        ))
        self.assertEqual(
            PostPagesTests.user.follower.count(),
            follow_count + 1,
        )
        follow = PostPagesTests.user.follower.last()
        self.assertEqual(follow.user, PostPagesTests.user)
        self.assertEqual(follow.author, PostPagesTests.user_2)

    def test_posts_auth_user_can_not_follow_myself(self):
        """Авторизованный пользователь не может подписаться на себя"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user.username}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTests.user,
                author=PostPagesTests.user,
            ).exists()
        )

    def test_posts_auth_user_can_not_follow_twice(self):
        """Авторизованный пользователь не может подписаться
        на другого автора дважды"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user_2.username}
        ))
        follow_count = Follow.objects.filter(
            user=PostPagesTests.user,
            author=PostPagesTests.user_2,
        ).count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user_2.username}
        ))
        self.assertEqual(
            follow_count,
            Follow.objects.filter(
                user=PostPagesTests.user,
                author=PostPagesTests.user_2,
            ).count()
        )

    def test_posts_follow_index_context(self):
        """Проверяем,что шаблон follow_index сформирован с правильным
        контекстом при наличии подписки"""
        Follow.objects.create(
            user=PostPagesTests.user_2,
            author=PostPagesTests.user,
        )
        new_post = Post.objects.create(
            author=PostPagesTests.user,
            text='Тестовая запись',
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertIn(new_post, response.context['page_obj'])
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_posts_unfollow_index_context(self):
        """Проверяем,что шаблон follow_index сформирован с правильным
        контекстом при отсутствии подписки"""
        new_post = Post.objects.create(
            author=PostPagesTests.user_2,
            text='Тестовая запись',
        )
        self.assertFalse(Follow.objects.filter(
            user=PostPagesTests.user,
            author=PostPagesTests.user_2
        ).exists())
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context['page_obj'])
