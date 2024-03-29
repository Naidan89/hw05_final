from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test_group',
            slug='test_slug',
            description='Тестовое описание',
        )

    def test_index_cache(self):
        cache_post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый пост'
        )
        response = self.client.get(reverse('posts:index'))
        cache1 = response.content
        cache_post.delete()
        response2 = self.client.get(reverse('posts:index'))
        cache2 = response2.content
        self.assertTrue(cache1 == cache2)
        cache.clear()
        response3 = self.client.get(reverse('posts:index'))
        cache3 = response3.content
        self.assertTrue(cache1 != cache3)
