from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        expected_title = 'Заголовок тестовой группы'
        self.assertEqual(expected_title, str(group))
        expected_text_post = 'тестовый пост'
        self.assertEqual(expected_text_post, str(post))
