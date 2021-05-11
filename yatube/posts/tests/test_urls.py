from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.user_2 = User.objects.create_user(username='TestUser2')
        cls.group = Group.objects.create(
            title='Тестовое имя группы',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста 1 (1 юзер)',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def tearDown(self):
        cache.clear()

    def test_homepage_exists(self):
        '''Главная страница доступна всем'''
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page_exists(self):
        '''Доступ к странице группы доступен всем'''
        response = self.guest_client.get('/group/test_group/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_page_exists(self):
        '''Доступ к странице профиля пользователя доступен всем'''
        response = self.guest_client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_page_exists(self):
        '''Доступ к странице поста пользователя доступен всем'''
        response = self.guest_client.get(
            f'/{self.user.username}/{self.post.id}/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_newpost_page_nonauth_redirects(self):
        '''Страница new перенаправляет анонимного пользователя'''
        response = self.guest_client.get('/new/')
        self.assertRedirects(response, reverse('login')
                             + '?next=' + reverse('new_post'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_newpost_page_auth_exists(self):
        '''Страница new доступна авторизированному пользователю'''
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_editpost_nonauth_redirects(self):
        '''Страница edit перенаправляет анонимного пользователя'''
        url = f'{self.user.username}/{self.post.id}/edit/'
        response = self.guest_client.get(f'/{url}')
        redirect = (reverse('login') + f'?next=/{url}')
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_editpost_wrongauth_redirects(self):
        '''Страница edit перенаправляет пользователя, не
        являющегося автором поста'''
        url_post = f'/{self.user.username}/{self.post.id}/'
        response = self.authorized_client_2.get(f'{url_post}edit/')
        self.assertRedirects(response, url_post)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_editpost_auth_exists(self):
        '''Страница edit доступна автору поста'''
        response = self.authorized_client.get(
            f'/{self.user.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_index_auth_exists(self):
        '''Страница follow_index доступна авторизированному пользователю'''
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_index_unauth_redirects(self):
        '''Страница follow_index перенаправляет анонимного пользователя'''
        response = self.guest_client.get('/follow/')
        redirect = (reverse('login') + '?next=/follow/')
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comment_anyone_redirects(self):
        '''Страница comment недоступна для всех пользователей'''
        # Для гостей - переход на страницу авторизации
        url_post = f'/{self.user.username}/{self.post.id}/'
        response = self.guest_client.get(f'{url_post}comment/')
        redirect = (reverse('login') + f'?next={url_post}comment/')
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Для авторизированных пользователей - на страницу поста
        response = self.authorized_client.get(f'{url_post}comment/')
        self.assertRedirects(response, url_post)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_page_not_found_returns_404(self):
        '''Возвращает ли сервер код 404, если страница не найдена'''
        response = self.guest_client.get('/not/a/page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names_unauth = {
            '/': 'index.html',
            f'/{self.user.username}/': 'profile.html',
            f'/{self.user.username}/{self.post.id}/': 'post.html',
            f'/group/{self.group.slug}/': 'group.html',
        }

        templates_url_names_auth = {
            '/new/': 'new_post.html',
            f'/{self.user.username}/{self.post.id}/edit/': 'new_post.html',
            '/follow/': 'follow.html'
        }
        for adress, template in templates_url_names_auth.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template, str(template))

        for adress, template in templates_url_names_unauth.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template, str(template))
