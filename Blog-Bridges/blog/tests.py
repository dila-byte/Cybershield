from django.test import TestCase
from django.contrib.auth import get_user_model
from blog.models import Post
from django.urls import reverse

User = get_user_model()

class UserModelTests(TestCase):
    def test_mysql_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(user.create_mysql_user())
        self.assertTrue(user.is_db_user_created)
        self.assertIsNotNone(user.mysql_password)

class PermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin',
            email='thiwa528@gmail.com',
            password='adminpass',
            is_staff=True
        )
        cls.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass'
        )
        cls.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=cls.admin
        )

    def test_admin_delete_permission(self):
        self.client.login(email='thiwa528@gmail.com', password='adminpass')
        response = self.client.post(reverse('delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect after success

    def test_regular_user_delete_permission(self):
        self.client.login(email='regular@example.com', password='regularpass')
        response = self.client.post(reverse('delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 403)  # Should be forbidden
