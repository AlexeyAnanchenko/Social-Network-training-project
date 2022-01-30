from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        model_str_dict = {
            post: post.text[:15],
            group: group.title,
            comment: comment.text[:20],
        }
        for model, expected_name_object in model_str_dict.items():
            with self.subTest(model=model):
                self.assertEqual(expected_name_object, str(model))

    def test_verbose_name_post(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text_post(self):
        """help_text в полях модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_verbose_name_comment(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым"""
        comment = PostModelTest.comment
        field_verboses = {
            'post': 'Пост',
            'text': 'Текст комментария',
            'created': 'Дата и время публикации',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_comment(self):
        """help_text в полях модели Comment совпадает с ожидаемым."""
        comment = PostModelTest.comment
        field_help_texts = {
            'text': 'Введите текст комментария',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text, expected_value)

    def test_posts_user_can_not_follow_twice(self):
        """Пользователь не может подписатьсяна другого автора дважды"""
        Follow.objects.create(
            user=PostModelTest.user_2,
            author=PostModelTest.user
        )
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=PostModelTest.user_2,
                author=PostModelTest.user
            )

    def test_posts_user_can_not_follow_myself(self):
        """Пользователь не может подписаться сам на себя"""
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=PostModelTest.user,
                author=PostModelTest.user
            )
