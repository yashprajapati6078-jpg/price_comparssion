import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app, db, Product, Category, Retailer, User

class ElectronicsCompareTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        with self.app.app_context():
            test_user = User.query.filter((User.username == 'validuser_99') | (User.email == 'validuser99@rigrate.com')).first()
            if test_user:
                db.session.delete(test_user)
                db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            test_user = User.query.filter((User.username == 'validuser_99') | (User.email == 'validuser99@rigrate.com')).first()
            if test_user:
                db.session.delete(test_user)
                db.session.commit()

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

    def test_auth_validation(self):
        # 1. Login with empty credentials
        res_empty_login = self.client.post('/login', data={'username': '', 'password': ''}, follow_redirects=True)
        self.assertIn(b'Please enter your username', res_empty_login.data)

        # 2. Login with email
        res_email_login = self.client.post('/login', data={'username': 'admin@rigrate.com', 'password': 'admin123'}, follow_redirects=True)
        self.assertIn(b'Welcome back, admin!', res_email_login.data)

        # Logout
        self.client.get('/logout')

        # 3. Login with wrong password
        res_wrong_pass = self.client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', res_wrong_pass.data)

        # 4. Register with invalid username (spaces, too short)
        res_short_user = self.client.post('/register', data={
            'username': 'ab',
            'email': 'valid@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Username must be between 3 and 30 characters', res_short_user.data)

        # 5. Register with invalid email
        res_bad_email = self.client.post('/register', data={
            'username': 'newuser1',
            'email': 'not-an-email',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Please enter a valid email address', res_bad_email.data)

        # 6. Register with short password
        res_short_pass = self.client.post('/register', data={
            'username': 'newuser2',
            'email': 'new2@example.com',
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        self.assertIn(b'Password must be at least 6 characters', res_short_pass.data)

        # 7. Register with mismatched confirm password
        res_mismatch = self.client.post('/register', data={
            'username': 'newuser3',
            'email': 'new3@example.com',
            'password': 'password123',
            'confirm_password': 'password456'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', res_mismatch.data)

        # 8. Register with duplicate username
        res_dup_user = self.client.post('/register', data={
            'username': 'admin',
            'email': 'distinct@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Username is already taken', res_dup_user.data)

        # 9. Register with duplicate email
        res_dup_email = self.client.post('/register', data={
            'username': 'uniquename99',
            'email': 'admin@rigrate.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email address is already registered', res_dup_email.data)

        # 10. Successful registration with valid data
        res_success = self.client.post('/register', data={
            'username': 'validuser_99',
            'email': 'validuser99@rigrate.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', res_success.data)


if __name__ == '__main__':
    unittest.main()


