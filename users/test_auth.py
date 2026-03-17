from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User

class AuthTests(APITestCase):
    def test_registration_with_phone(self):
        """Test registering a user with a full phone number."""
        url = reverse('api_register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+919876543210',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username='testuser').phone_number, '+919876543210')

    def test_login_with_phone(self):
        """Test logging in with a full phone number."""
        # First register
        user = User.objects.create_user(
            username='phoneuser',
            email='phone@example.com',
            phone_number='+919876543210',
            password='Password123!'
        )
        
        url = reverse('api_login')
        data = {
            'phone_number': '+919876543210',
            'password': 'Password123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'phone@example.com')

    def test_login_with_email(self):
        """Test logging in with email still works."""
        user = User.objects.create_user(
            username='emailuser',
            email='email@example.com',
            password='Password123!'
        )
        
        url = reverse('api_login')
        data = {
            'email': 'email@example.com',
            'password': 'Password123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
