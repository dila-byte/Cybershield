from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import MySQLdb
import re

class CustomUser(AbstractUser):
    is_db_user_created = models.BooleanField(default=False)
    mysql_password = models.CharField(max_length=128, blank=True, null=True)  # Store separate MySQL password
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def create_mysql_user(self):
        """Create a MySQL user with limited privileges for this user"""
        if self.is_db_user_created:
            return True
            
        sanitized_username = self.sanitize_mysql_username(self.username)
        password = self.__class__.objects.make_random_password(length=16)  # Changed from User to self.__class__
        
        try:
            conn = MySQLdb.connect(
                host=settings.DATABASES['default']['HOST'],
                user=settings.MYSQL_ADMIN_USER,
                passwd=settings.MYSQL_ADMIN_PASSWORD,
                port=int(settings.DATABASES['default']['PORT'])
            )
            
            cursor = conn.cursor()
            
            # Create user with limited privileges
            cursor.execute(f"CREATE USER '{sanitized_username}'@'%' IDENTIFIED BY '{password}'")
            cursor.execute(f"GRANT SELECT, INSERT ON {settings.DATABASES['default']['NAME']}.* TO '{sanitized_username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            
            conn.close()
            
            # Store the MySQL password
            self.mysql_password = password
            self.is_db_user_created = True
            self.save()
            return True
        except Exception as e:
            print(f"Error creating MySQL user: {e}")
            return False
    
    @staticmethod
    def sanitize_mysql_username(username):
        """Sanitize username for MySQL user creation"""
        return re.sub(r'[^a-zA-Z0-9_]+', '_', username)[:32]

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title