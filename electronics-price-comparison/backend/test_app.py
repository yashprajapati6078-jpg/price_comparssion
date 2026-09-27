import unittest
from app import app, db, Product, Category, Retailer, User

class ElectronicsCompareTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'RigRate', response.data)

    def test_search_api(self):
        response = self.client.get('/api/products/search?q=iPhone')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(len(data) > 0)
        self.assertIn('iPhone', data[0]['name'])

    def test_categories_api(self):
        response = self.client.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 9)

    def test_price_history_api(self):
        with self.app.app_context():
            p = Product.query.first()
            p_id = p.id
        response = self.client.get(f'/api/products/{p_id}/history')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('labels', data)
        self.assertIn('datasets', data)

    def test_auth_pages(self):
        response_login = self.client.get('/login')
        self.assertEqual(response_login.status_code, 200)
        self.assertIn(b'Welcome Back', response_login.data)

        response_register = self.client.get('/register')
        self.assertEqual(response_register.status_code, 200)
        self.assertIn(b'Create Account', response_register.data)

    def test_admin_routes_authorized(self):
        # Log in as admin user
        with self.client:
            self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
            
            res_dash = self.client.get('/admin')
            self.assertEqual(res_dash.status_code, 200)

            res_prod = self.client.get('/admin/products')
            self.assertEqual(res_prod.status_code, 200)

            res_cat = self.client.get('/admin/categories')
            self.assertEqual(res_cat.status_code, 200)

            res_ret = self.client.get('/admin/retailers')
            self.assertEqual(res_ret.status_code, 200)

    def test_product_details_page(self):
        with self.app.app_context():
            p = Product.query.first()
            p_id = p.id
        response = self.client.get(f'/product/{p_id}')
        self.assertEqual(response.status_code, 200)

    def test_external_price_lookup_api(self):
        # Test empty query validation
        res_empty = self.client.get('/api/prices/lookup')
        self.assertEqual(res_empty.status_code, 400)

        # Test query with or without key configured returns valid schema
        res_lookup = self.client.get('/api/prices/lookup?q=Sony+WH-1000XM5')
        data = res_lookup.get_json()
        if res_lookup.status_code == 200:
            self.assertTrue(data.get('success'))
            self.assertIn('prices', data)
        else:
            self.assertEqual(res_lookup.status_code, 400)
            self.assertFalse(data['success'])
            self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()

