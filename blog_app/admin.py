from django.contrib import admin
from .models import BlogPost, User, Message, Order, Notification, Product, ProductOrder, BlogLikes

# Register your models here.
admin.site.register(BlogPost)
admin.site.register(User)
admin.site.register(Message)
admin.site.register(Order)
admin.site.register(Notification)
admin.site.register(Product)
admin.site.register(ProductOrder)
admin.site.register(BlogLikes)