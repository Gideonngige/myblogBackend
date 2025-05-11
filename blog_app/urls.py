from django.urls import path
from . import views

urlpatterns = [
    path('members/', views.members, name='members'),
    path('postblog/', views.postblog, name='postblog'),
    path('get_blog_posts/', views.get_blog_posts, name='get_blog_posts'),
]