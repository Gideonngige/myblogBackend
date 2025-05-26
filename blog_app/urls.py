from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('postblog/', views.postblog, name='postblog'),
    path('get_blog_posts/', views.get_blog_posts, name='get_blog_posts'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('send_message/', views.send_message, name='send_message'),
    path('create_order/', views.create_order, name='create_order'),
    path('get_user_notifications/<int:user_id>/', views.get_user_notifications, name='get_user_notifications'),
    path('add_product/', views.add_product, name='add_product'),
    path('get_products/', views.get_products, name='get_products'),
]