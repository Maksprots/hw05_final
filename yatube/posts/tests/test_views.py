from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Group, Follow
from django import forms
from django.core.cache import cache

User = get_user_model()

TEXT_TEST = 'тестовый пост'


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # юзер 1 автор постов
        cls.user = User.objects.create_user(username='NoName')
        # юзер 2 автор постов
        cls.user_2 = User.objects.create_user(username='author2')
        # юзер подписан на автора
        cls.user_follower = User.objects.create_user(username='user_follower')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test_slug2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='тестовый пост',
            author=cls.user,
            group=cls.group,
        )

        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )
        cls.follow_filter = Follow.objects.filter(
            user=cls.user_follower,
            author=cls.user
        )

        for i in range(13):
            cls.posts = Post.objects.create(
                text='тестовый пост',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)
        self.guest_client = Client()
        self.follower_client = Client()
        self.follower_client.force_login(self.user_follower)
        self.user2_client = Client()
        self.user2_client.force_login(self.user_2)

    def test_view_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
            reverse('about:author'):
                'about/author.html',
            reverse('about:tech'):
                'about/tech.html',
            reverse('posts:follow_index'):
                'posts/follow.html',
        }
        cache.clear()
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorised_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_test(self, response):
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        self.assertEqual(post_text, 'тестовый пост')
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, self.group)

    def test_correct_context_index(self):
        # cache.clear()
        response = self.authorised_client.get(reverse('posts:index'))
        self.post_test(response)
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index(self):
        # cache.clear()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_correct_context_group_list(self):
        cache.clear()
        response = self.authorised_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}))
        self.post_test(response)
        group_obj = response.context['group']
        self.assertEqual(group_obj, self.group)
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_group_list(self):

        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_correct_context_profile(self):
        # cache.clear()
        response = self.authorised_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}))
        self.post_test(response)
        author_obj = response.context['author']
        self.assertEqual(author_obj, self.user)
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_profile(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_correct_context_post_detail(self):
        response = self.authorised_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        post_obj = response.context['post']
        author_obg = response.context['author']
        self.assertEqual(post_obj, self.post)
        self.assertEqual(author_obg, self.user)

    def test_correct_context_create_post(self):
        response = self.authorised_client.get(
            reverse('posts:post_create'))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_context_post_edit(self):
        response = self.authorised_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        is_edit_context = response.context['is_edit']
        post_id_context = response.context['post_id']
        self.assertEqual(is_edit_context, True)
        self.assertEqual(post_id_context, self.post.id)

    def test_correct_group_of_post(self):
        response = self.authorised_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug2'}))
        group_obj = response.context['page_obj']
        self.assertNotIn(self.post, group_obj)

    def test_add_comment_no_auth(self):
        response = self.guest_client.get(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk})
        )
        template = '/auth/login/?next=/posts/1/comment/'
        self.assertRedirects(response, template)

    def test_cache(self):
        response1 = self.guest_client.get(
            reverse('posts:index')).content
        Post.objects.create(
            text='тестовый постttt',
            author=self.user,
            group=self.group,
        )
        response2 = self.guest_client.get(
            reverse('posts:index')).content
        self.assertEqual(response1, response2)
        cache.clear()
        response3 = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(response1, response3)

    def test_following_user(self):
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower,
            author=self.user
        ).exists())

    def test_follow_index_follower(self):
        posts_before_add_post = Post.objects.filter(
            author__following__user=self.user_follower)
        count_before_add_post = posts_before_add_post.count()
        Post.objects.create(
            text='тестовый пост',
            author=self.user,
            group=self.group,
        )
        posts_after_add_post = Post.objects.filter(
            author__following__user=self.user_follower)
        count_after_add_post = posts_after_add_post.count()
        self.assertEqual(count_before_add_post + 1, count_after_add_post)

    def test_follow_index_unfollower(self):
        posts_before_add_post = Post.objects.filter(
            author__following__user=self.user)
        count_before_add_post = posts_before_add_post.count()
        Post.objects.create(
            text='тестовый пост',
            author=self.user_2,
            group=self.group,
        )
        posts_after_add_post = Post.objects.filter(
            author__following__user=self.user)
        count_after_add_post = posts_after_add_post.count()
        self.assertEqual(count_before_add_post, count_after_add_post)

    def test_unfollow_user(self):
        self.follow.delete()
        self.assertFalse(self.follow_filter.exists())
