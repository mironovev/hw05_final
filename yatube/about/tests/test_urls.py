from http import HTTPStatus

from django.test import TestCase, Client


class AboutURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_exist(self):
        '''Статические страницы доступны всем'''
        static_pages = [
            '/about/author/',
            '/about/tech/',
        ]
        for url in static_pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_urls_use_correct_templates(self):
        '''Статические страницы используют верный шаблон'''
        templates_url_names = {
            '/about/author/': 'author.html',
            '/about/tech/': 'tech.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
