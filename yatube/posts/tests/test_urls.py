from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.public_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
        }
        cls.personal_urls = {
            '/create/': 'posts/post_create.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls(self):
        """Проверка доступности для общих страниц"""
        for url in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_personal_urls(self):
        """Проверка доступности для персональных страниц"""
        for url in self.personal_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_non_author(self):
        """Страница /post_edit/ не доступна не автору поста."""
        self.authorized_client.force_login(self.user2)
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        """Не существующая страница возвращает ошибку 404."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_guest_redirect(self):
        """Проверка редиректов для неавторизованного пользователя"""
        for url in self.personal_urls:
            redirect = f'/auth/login/?next={url}'
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = {**self.public_urls, **self.personal_urls}
        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
