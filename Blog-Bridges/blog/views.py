from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from blog import models
from .models import Post
from django.contrib.auth import authenticate, login, logout
from django.utils.html import escape
from django.http import HttpResponseForbidden
from django.conf import settings
import re
import MySQLdb

User = get_user_model()

# Utility function for MySQL username sanitization
def sanitize_mysql_username(username):
    """Sanitize username for MySQL user creation"""
    return re.sub(r'[^a-zA-Z0-9_]+', '_', username)[:32]

def create_mysql_user(username, password):
    """Create a MySQL user with limited privileges"""
    sanitized_username = sanitize_mysql_username(username)
    db_name = settings.DATABASES['default']['NAME']
    
    try:
        conn = MySQLdb.connect(
            host=settings.DATABASES['default']['HOST'],
            user=settings.MYSQL_ADMIN_USER,
            passwd=settings.MYSQL_ADMIN_PASSWORD,
            port=int(settings.DATABASES['default']['PORT'])
        )
        
        cursor = conn.cursor()
        cursor.execute(f"CREATE USER '{sanitized_username}'@'%' IDENTIFIED BY '{password}'")
        cursor.execute(f"GRANT SELECT, INSERT ON {db_name}.* TO '{sanitized_username}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating MySQL user: {e}")
        return False

def sanitize_input_based_on_role(user, input_data, field_name):
    """Role-based input sanitization"""
    if hasattr(user, 'email') and user.email in getattr(settings, 'ADMIN_EMAILS', []):
        # Admin - minimal sanitization
        return input_data.strip()
    else:
        # Regular user - strict sanitization
        sanitized = escape(input_data.strip())
        if field_name == 'username':
            return sanitize_mysql_username(sanitized)
        return sanitized

def signup(request):
    if request.method == 'POST':
        name = sanitize_input_based_on_role(None, request.POST.get('uname', ''), 'username')
        email = sanitize_input_based_on_role(None, request.POST.get('uemail', ''), 'email')
        password = request.POST.get('upassword', '')
        
        if not all([name, email, password]):
            return redirect('/signup')
            
        new_user = User.objects.create_user(username=name, email=email, password=password)
        
        # Create MySQL user with the same password (in production, use a different random password)
        if create_mysql_user(name, password):
            # In a real app, you'd want to store this status in your user model
            pass
            
        return redirect('/loginn')
    return render(request, 'blog/signup.html')

def loginn(request):
    if request.method == 'POST':
        name = sanitize_input_based_on_role(None, request.POST.get('uname', ''), 'username')
        password = request.POST.get('upassword', '')  # Don't escape passwords
        
        user = authenticate(request, username=name, password=password)
        
        if user is not None:
            login(request, user)
            
            # For admin users, switch to root MySQL connection
            if hasattr(user, 'email') and user.email in getattr(settings, 'ADMIN_EMAILS', []):
                from django.db import connections
                connections['default'].settings_dict['USER'] = getattr(settings, 'MYSQL_ADMIN_USER', 'root')
                connections['default'].settings_dict['PASSWORD'] = getattr(settings, 'MYSQL_ADMIN_PASSWORD', '')
                
            return redirect('/home')
        else:
            return redirect('/login')

    return render(request, 'blog/login.html')

def home(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)

def newPost(request):
    if not request.user.is_authenticated:
        return redirect('/loginn')
        
    if request.method == 'POST':
        title = sanitize_input_based_on_role(request.user, request.POST.get('title', ''), 'title')
        content = sanitize_input_based_on_role(request.user, request.POST.get('content', ''), 'content')
        
        npost = models.Post(title=title, content=content, author=request.user)
        npost.save()
        return redirect('/home')
    
    return render(request, 'blog/newpost.html')

def myPost(request):
    if not request.user.is_authenticated:
        return redirect('/loginn')
        
    context = {
        'posts': Post.objects.filter(author=request.user)
    }
    return render(request, 'blog/mypost.html', context)

def signout(request):
    logout(request)
    return redirect('/loginn')

def deletePost(request, post_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'email') or request.user.email not in getattr(settings, 'ADMIN_EMAILS', []):
        return HttpResponseForbidden("Only admin is allowed to delete posts.")
    
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('/home')