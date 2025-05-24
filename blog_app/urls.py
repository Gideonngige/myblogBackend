from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('postblog/', views.postblog, name='postblog'),
    path('get_blog_posts/', views.get_blog_posts, name='get_blog_posts'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
]