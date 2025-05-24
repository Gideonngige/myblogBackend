from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=20)
    profile_image = models.URLField()

class BlogPost(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', default=1)
    title = models.CharField(max_length=200)
    image = models.URLField()  # Stores Cloudinary URL
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)