from django.contrib import admin
from .models import BlogPost, User, Message

# Register your models here.
admin.site.register(BlogPost)
admin.site.register(User)
admin.site.register(Message)