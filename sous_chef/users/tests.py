# users/tests/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class UserRegistrationTestCase(APITestCase):
    def test_user_registration(self):
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'somepassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertTrue('password' not in response.data)