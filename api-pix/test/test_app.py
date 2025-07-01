import unittest
from app.main import create_app

class PixApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('API Pix Rodando', response.get_json()['message'])

    def test_hello(self):
        response = self.client.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Olá do endpoint', response.get_json()['message'])

if __name__ == '__main__':
    unittest.main()
