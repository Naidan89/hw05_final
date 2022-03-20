from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post


User = get_user_model()


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pedro')
        cls.user2 = User.objects.create_user(username='Hulio')
        cls.user3 = User.objects.create_user(username='Moralez')
        Follow.objects.create(user=cls.user, author=cls.user2)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow(self):
        """Проверка подписки"""
        authors = Follow.objects.filter(user=self.user)
        cnt = len(authors)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user3.username}))
        authors2 = Follow.objects.filter(user=self.user)
        cnt2 = len(authors2)
        self.assertEqual(cnt2, cnt + 1)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user3.username}))
        authors3 = Follow.objects.filter(user=self.user)
        cnt3 = len(authors3)
        self.assertEqual(cnt3, cnt)

    def test_follow_posts(self):
        """Проверка наличия поста подписки в ленте"""
        Post.objects.create(
            author=self.user2,
            text='Тестовый пост'
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_obj = response.context['page_obj'][0]
        self.assertEqual(post_obj.text, 'Тестовый пост')
        self.assertEqual(post_obj.author.username, 'Hulio')

    def test_follow_posts(self):
        """Проверка отсутствия поста подписки в ленте"""
        Post.objects.create(
            author=self.user2,
            text='Тестовый пост'
        )
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user3)
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        post_obj = len(response.context['page_obj'])
        self.assertEqual(post_obj, 0)

    def test_self_follow(self):
        authors = Follow.objects.filter(user=self.user)
        cnt = len(authors)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        authors2 = Follow.objects.filter(user=self.user)
        cnt2 = len(authors2)
        self.assertEqual(cnt2, cnt)
