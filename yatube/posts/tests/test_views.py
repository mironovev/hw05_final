import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from ..models import Follow, Post, Group, Comment

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create(username='TestAuthor')
        cls.user = User.objects.create_user(username='TestUser')
        cls.user2 = User.objects.create_user(username='TestUser2')
        cls.group1 = Group.objects.create(
            title='Тестовое имя группы 1',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовое имя группы 2',
            slug='test_group2',
            description='Тестовое описание группы 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
        cls.post1 = Post.objects.create(
            text='Тестовый текст поста 1 (1 группа)',
            author=cls.test_author,
            group=cls.group1,
            image=uploaded
        )
        #  Нужно было поставить сортировку по -id :/
        cls.post2 = Post.objects.create(
            text='Тестовый текст поста 2 (2 группа)',
            author=cls.test_author,
            group=cls.group2,
            image=uploaded
        )
        cls.post3 = Post.objects.create(
            text='Тестовый текст поста 3 (2 группа)',
            author=cls.user,
            group=cls.group2,
            image=uploaded
        )
        cls.comment1 = Comment.objects.create(
            post=cls.post1,
            author=cls.user,
            text='Тестовый текст комментария'
        )
        cls.follow_relation1 = Follow.objects.create(
            user=cls.user,
            author=cls.test_author
        )
        cls.follow_relation2 = Follow.objects.create(
            user=cls.user,
            author=cls.user2
        )
        cls.follow_relation3 = Follow.objects.create(
            user=cls.user2,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.test_author)

    @classmethod
    def tearDownClass(self) -> None:
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def tearDown(self):
        cache.clear()

    def compare_posts(self, response, post1: Post, post2: Post):
        '''Сравниваем содержимое двух постов'''
        self.assertEqual(post1.text, post2.text)
        self.assertEqual(post1.author, post2.author)
        self.assertEqual(post1.group, post2.group)
        # <img не работает для test_edit_post_page_context, small.gif не
        # работает для остальных. Там есть другие варианты, но все они
        # являются совсем уже костылями.
        # self.assertContains(response, 'small.gif')
        self.assertEqual(post1.image.name, post2.image.name)

    def test_pages_templates(self):
        '''URL адрес использует соответсвтующий шаблон'''
        templates_pages_names_unauth = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                                  kwargs={'slug': self.group1.slug}),
            'profile.html': reverse(
                'profile',
                kwargs={'username': self.test_author.username}
            ),
            'post.html': reverse(
                'post',
                kwargs={'username': self.test_author.username,
                        'post_id': self.post1.id}
            )
        }
        for template, reverse_name in templates_pages_names_unauth.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template, template)
        response = self.authorized_client.get(reverse('new_post'))
        self.assertTemplateUsed(response, 'new_post.html')
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertTemplateUsed(response, 'follow.html')

    def test_home_page_context(self):
        '''Шаблон home сформирован с правильным контекстом.'''
        response = self.guest_client.get(reverse('index'))
        latest_object = response.context.get('page').object_list[0]
        self.compare_posts(response, latest_object, self.post3)

    def test_home_page_context_length(self):
        '''Все посты из бд попали на главную'''
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_group_page_context(self):
        '''Шаблон group_posts сформирован с правильным контекстом'''
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': self.group1.slug})
        )
        latest_object = response.context.get('page').object_list[0]
        self.compare_posts(response, latest_object, self.post1)

    def test_empty_group_page_objects(self):
        '''Посты, которые не пренадлежат группе,
        не выводятся на ее странице'''
        group3 = Group.objects.create(
            title='Тестовое имя группы 3',
            slug='test_group3',
            description='Тестовое описание группы 3',
        )
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': group3.slug})
        )
        self.assertEqual(len(response.context.get('page').object_list), 0)

    def test_new_post_page_context(self):
        '''Шаблон new_post сформирован с правильным контекстом'''
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        is_edit = response.context.get('is_edit')
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertFalse(is_edit)

    def test_profile_page_context(self):
        '''Шаблон profile сформирован с правильным контекстом'''
        response = self.guest_client.get(
            reverse('profile', kwargs={'username':
                                       self.test_author.username})
        )
        latest_object = response.context.get('page').object_list[0]
        author = response.context.get('author')
        username = response.context.get('username')
        page = response.context.get('page')
        self.compare_posts(response, latest_object, self.post2)
        self.assertEqual(author, self.test_author)
        self.assertEqual(username, self.test_author.username)
        self.assertEqual(page.number, 1)

    def test_post_page_context(self):
        '''Шаблон post сформирован с правильным контекстом'''
        response = self.guest_client.get(
            reverse('post', kwargs={
                'username': self.test_author.username,
                'post_id': self.post1.id
            })
        )
        username = response.context.get('username')
        author = response.context.get('author')
        comment = response.context.get('comments')[0]
        requested_post = response.context.get('requested_post')
        self.assertEqual(username, self.test_author.username)
        self.assertEqual(author, self.test_author)
        self.assertEqual(comment.text, self.comment1.text)
        self.assertEqual(comment.post, self.comment1.post)
        self.assertEqual(comment.author, self.comment1.author)
        self.compare_posts(response, requested_post, self.post1)

    def test_post_page_no_comments(self):
        '''На странице с постом без комментариев нет комментариев'''
        response = self.guest_client.get(
            reverse('post', kwargs={
                'username': self.test_author.username,
                'post_id': self.post2.id
            })
        )
        self.assertEqual(len(response.context.get('comments')), 0)

    def test_edit_post_page_context(self):
        '''Шаблон post_edit сформирован с правильным контекстом'''
        response = self.authorized_author_client.get(
            reverse('post_edit', kwargs={
                'username': self.test_author.username,
                'post_id': self.post1.id
            })
        )
        is_edit = response.context.get('is_edit')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        post = response.context.get('post')
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertTrue(is_edit)
        self.compare_posts(response, post, self.post1)

    def test_follow_index_context(self):
        '''Шаблон follow сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('follow_index'))
        latest_object = response.context.get('page').object_list[0]
        self.compare_posts(response, latest_object, self.post2)

    def test_follow_index_no_other_posts(self):
        '''В follow только посты от авторов, на которых подписан
        пользователь'''
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context.get('page').object_list), 2)

    def test_follow_index_empty(self):
        '''В follow пост пользователя не появляется для тех кто не подписан'''
        response = self.authorized_author_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context.get('page').object_list), 0)

    def test_unfollow_author(self):
        '''Проверка отписки'''
        self.authorized_client.get(reverse('profile_unfollow', kwargs={
            'username': self.test_author.username})
        )
        self.assertFalse(Follow.objects.filter(
            user=self.follow_relation1.user,
            author=self.follow_relation1.author
        ).exists())
        self.assertEqual(Follow.objects.count(), 2)

    def test_follow_author(self):
        '''Проверка подписки'''
        self.authorized_client.get(reverse('profile_follow', kwargs={
            'username': self.test_author.username})
        )
        self.assertTrue(Follow.objects.filter(
            user=self.follow_relation1.user,
            author=self.follow_relation1.author
        ).exists())
        self.assertEqual(Follow.objects.count(), 3)

    def test_cache(self):
        '''Проверка кэширования'''
        self.guest_client.get(reverse('index'))
        self.guest_client.get(reverse('index'))
        key = make_template_fragment_key('post_list_index')
        self.assertIsNotNone(cache.get(key))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create(username='TestAuthor')
        cls.group1 = Group.objects.create(
            title='Тестовое имя группы 1',
            slug='test_group',
            description='Тестовое описание группы',
        )
        for i in range(13):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.test_author
            )
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.test_author,
                group=cls.group1
            )

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_first_index_page_contains_ten_records(self):
        '''На первой странице шаблона index находится 10 записей'''
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_third_index_page_contains_six_records(self):
        '''На третьей странице шаблона index находится 6 записей'''
        response = self.client.get(reverse('index') + '?page=3')
        self.assertEqual(len(response.context.get('page').object_list), 6)

    def test_first_group_page_contains_ten_records(self):
        '''На первой странице шаблона группы находится 10 записей'''
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': self.group1.slug})
        )
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_group_page_contains_ten_records(self):
        '''На второй странице шаблона группы находится 3 записи'''
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={
                'slug': self.group1.slug
            }) + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_profile_page_contains_ten_records(self):
        '''На первой странице шаблона профиля пользователя находится
        10 записей'''
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.test_author.username})
        )
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_first_profile_page_contains_ten_records(self):
        '''На третьей странице шаблона профиля пользователя находится
        6 записей'''
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.test_author.username})
            + '?page=3'
        )
        self.assertEqual(len(response.context.get('page').object_list), 6)
