from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group

User = get_user_model()

USERNAME_AUTHOR = 'NoName'
USERNAME_NOT_AUTHOR = 'not_auth'
TEXT_TEST = 'тестовый пост'
SLUG_TEST = 'test'
TITLE_TEST = 'Заголовок тестовой группы'
DESCRIPTION_TEST = 'Тестовое описание'
UNEXISTING_PAGE = 'posts/unexisting_page/'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT_TEST,
        )
        cls.user_not_author = User.objects.create_user(
            username=USERNAME_NOT_AUTHOR)
        cls.group = Group.objects.create(
            title=TITLE_TEST,
            slug=SLUG_TEST,
            description=DESCRIPTION_TEST,
        )

        cls.templates_url_names_common = \
            {'/group/test/': 'posts/group_list.html',
             f'/profile/{USERNAME_AUTHOR}/': 'posts/profile.html',
             f'/posts/{cls.post.id}/': 'posts/post_detail.html',
             '/': 'posts/index.html',
             '/about/author/': 'about/author.html',
             '/about/tech/': 'about/tech.html',
             }
        cls.templates_url_redirect_common = {
            '/create/':
                '/auth/login/?next=/create/',
            f'/posts/{cls.post.id}/edit/':
                f'/auth/login/?next=/posts/{cls.post.id}/edit/',
        }
        cls.template_name_authorized_users = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/follow/': 'posts/follow.html',

        }
        cls.templates_auth_but_not_author = {
            f'/posts/{cls.post.id}/edit/': f'/posts/{cls.post.id}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author = Client()
        self.not_author.force_login(self.user_not_author)

    def test_urls_common_users(self):
        """Тесты для проверки общедоступных страниц"""
        for address, template in self.templates_url_names_common.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_common_users(self):
        """Тесты для проверки редиректов неавторизованного пользователя"""
        for address, template in self.templates_url_redirect_common.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, template)

    def test_urls_authorized_users(self):
        """Тесты для проверки страниц авторизованного пользователя"""
        for address, template in self.template_name_authorized_users.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_urls_auth_not_author(self):
        """Тесты для проверки редиректов,
        если пост редактирует не автор поста"""
        for address, template in self.templates_auth_but_not_author.items():
            with self.subTest(address=address):
                response = self.not_author.get(address, follow=True)
                self.assertRedirects(response, template)

    def test_unexisting_page(self):
        response = self.guest_client.get(UNEXISTING_PAGE)
        self.assertEqual(response.status_code, 404)

    # страница follow тестируется в одном из сабтестов
    def test_comment_url(self):
        url = f'/posts/{self.post.id}/comment/'
        response = self.authorized_client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_follow_btn_urls(self):
        url_follow = f'/profile/{self.user.username}/follow/'
        response = self.authorized_client.post(url_follow, follow=True)
        self.assertEqual(response.status_code, 200)
