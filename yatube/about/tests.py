from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_static_address(self):
        """Проверка доступности адресов /about/."""
        static_address = ['/about/author/', '/about/tech/']
        for address in static_address:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_about_static_template(self):
        """Проверка шаблона для адреса /about/."""
        static_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in static_template.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
