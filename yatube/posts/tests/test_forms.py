from ..models import Post, Comment
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
TEXT_COMMENT = 'test comment'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name')

        cls.post = Post.objects.create(
            text='тестовый пост',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='test comment'
        )

    def setUp(self):
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_correct_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
            'text': 'тестовый пост',
            'image': uploaded,
        }
        response = self.authorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'Name'}))
        self.assertTrue(
            Post.objects.filter(
                text='тестовый пост',
                author=self.user,
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_uncorrect_create_post(self):
        uploaded = SimpleUploadedFile(
            name='small.txt',
            content=b'\x00\x00\x00\x2C\x00\x00\x00\x00',
        )
        form_data = {
            'text': 'тестовый пост',
            'image': uploaded,
        }
        response = self.authorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(response,
                             form='form',
                             field='image',
                             errors=[]
                             )

    def test_correct_edit_post(self):
        form_data = {
            'text': 'тестовый посt',
        }
        post_old_text = self.post.text
        post_old_image = self.post.image
        self.authorised_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data)
        post_new = Post.objects.get(pk=self.post.pk)
        self.assertNotEqual(post_old_text, post_new.text)
        self.assertEqual(post_old_image, post_new.image)

    def test_display_comment_on_the_page(self):
        form_data = {
            'text': TEXT_COMMENT
        }
        self.authorised_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data)
        self.assertTrue(
            Comment.objects.filter(
                text=TEXT_COMMENT))
