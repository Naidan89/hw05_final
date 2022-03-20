from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Comment, Group, Post


User = get_user_model()

FIRST_PAGE_POSTS = 10
SECOND_PAGE_POSTS = 3
ALL_POSTS = FIRST_PAGE_POSTS + SECOND_PAGE_POSTS


class PostViewTests(TestCase):
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
        Post.objects.bulk_create([
            Post(author=cls.user,
                 group=cls.group,
                 text=f'Тестовый пост {i}')
            for i in range(ALL_POSTS)
        ])
        cls.post = Post.objects.get(pk=4)
        Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент'
        )
        cls.templates_page_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}):
            'posts/post_create.html',
        }
        cls.urls_check_pagination = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.user.username}):
            'posts/profile.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблоны сформирован с правильным контекстом."""
        for reverse_name in self.urls_check_pagination:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                post_obj = response.context['page_obj'][0]
                self.assertEqual(post_obj.text, 'Тестовый пост 12')
                self.assertEqual(post_obj.group.slug, 'test_slug')
                self.assertEqual(post_obj.author.username, 'auth')

    def test_first_page_contains_ten_records(self):
        """Проверка паджинации: 10"""
        pages = (
            (1, FIRST_PAGE_POSTS),
            (2, SECOND_PAGE_POSTS),
        )
        for page, count in pages:
            for url in self.urls_check_pagination:
                with self.subTest(url=url):
                    response = self.client.get(url, {"page": page})
                    self.assertEqual(
                        len(response.context["page_obj"].object_list), count
                    )

    def test_post_detail_correct_context_list(self):
        """Шаблон post_detail сформирован правильно."""
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context['post']
        post2 = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post, post2)

    def test_create_post_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_guest_comments(self):
        """Гость не может комментить"""
        comm_count = self.post.comments.count()
        form_data = {
            'text': 'Тестовый коммент 2'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        comm_count2 = self.post.comments.count()
        self.assertEqual(comm_count, comm_count2)
        self.assertRedirects(response, '/auth/login/?next=/posts/4/comment/')

    def test_author_comments(self):
        """Авторизованный может комментить"""
        comm_count = self.post.comments.count()
        form_data = {
            'text': 'Тестовый коммент 2'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        comm_count2 = self.post.comments.count()
        self.assertEqual(comm_count + 1, comm_count2)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
