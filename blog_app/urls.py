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
    path('add_stock/<int:product_id>/<int:additional_stock>/', views.add_stock, name='add_stock'),
    path('create_product_order/', views.create_product_order, name='create_product_order'),
    path('get_product_orders/<int:user_id>/', views.get_product_orders, name='get_product_orders'),
    path('get_all_orders/', views.get_all_orders, name='get_all_orders'),
    path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),
]