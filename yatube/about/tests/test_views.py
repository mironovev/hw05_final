from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имени about:<имя_страницы>,
        доступен."""
        gen_url = [
            'about:author',
            'about:tech'
        ]
        for url in gen_url:
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url))
                self.assertEqual(response.status_code, 200)

    def test_static_page_uses_correct_template(self):
        """При запросе к about:<имя_страницы>
        применяется корректный шаблон."""
        templates_url_names = {
            'about:author': 'author.html',
            'about:tech': 'tech.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse(adress))
                self.assertTemplateUsed(response, template)
