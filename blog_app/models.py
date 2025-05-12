from django.db import models

# Create your models here.
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField()  # Stores Cloudinary URL
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Users(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=20)
    profile_image = models.URLField()