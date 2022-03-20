import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group2 = Group.objects.create(
            title='Test_group2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""

        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group='1',
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_post_create(self):
        """Неавторизованный пользователь не создает запись в Post."""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), tasks_count)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""

        post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый пост'
        )
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group2.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post.pk}))
        edited_post = Post.objects.get(pk=post.pk)
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertEqual(edited_post.group, self.group2)
        self.assertEqual(edited_post.text, 'Тестовый текст 2')

    def test_context_image(self):
        """Тест наличия картинки в словарях context."""
        cache.clear()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
            image=self.uploaded
        )
        urls_check_image = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
            reverse('posts:post_detail', kwargs={'post_id': post.pk}),
        )
        for pages in urls_check_image:
            with self.subTest(pages=pages):
                response = self.guest_client.get(pages)
                image = response.context.get('post')
                expected = post.image
                self.assertEqual(image.image, expected)
