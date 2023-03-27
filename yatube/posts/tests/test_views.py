from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()
TEST_OF_POST = 13


class ViewsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug='slug_slug',
            description='Новое описание',
        )

        cls.new_post = Post.objects.create(
            author=cls.user,
            text='Новый пост',
            group=cls.new_group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = ViewsURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': f'{self.user}'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][1]
        posts_author = first_object.author
        post_text = first_object.text
        self.assertEqual(posts_author, ViewsURLTests.user)
        self.assertEqual(post_text, ViewsURLTests.post.text)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        self.assertEqual(response.context.get('group').slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': f'{self.user}'}))
        first_object = response.context['page_obj'][1]
        posts_author = first_object.author
        self.assertEqual(posts_author, ViewsURLTests.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id':
                                                 f'{self.post.id}'}))
        self.assertEqual(response.context.get(
            'post').author, ViewsURLTests.user)
        self.assertEqual(response.context.get(
            'post').text, ViewsURLTests.post.text)
        self.assertEqual(response.context.get(
            'post').group, ViewsURLTests.post.group)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_on_page_index_profile_group_list(self):
        """Пост появляется на index, group_list, profile."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.new_post.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user}'})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.new_post, response.context['page_obj'])

    def test_post_not_for_your_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        self.assertNotIn(self.new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        self.posts = Post.objects.bulk_create(
            [Post(
                author=self.user,
                text=f'Тестовый пост {i}',
                group=self.group)
                for i in range(TEST_OF_POST)]
        )

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={'username': f'{self.user}'})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_NUM)

    def test_second_page_contains_three_records(self):
        """Количество постов на первой странице равно 3."""
        templates_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={'username': f'{self.user}'})
        )
        for reverse_name in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    TEST_OF_POST - settings.POSTS_NUM)
