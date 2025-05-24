from django.contrib import admin
from .models import BlogPost, User

# Register your models here.
admin.site.register(BlogPost)
admin.site.register(User)