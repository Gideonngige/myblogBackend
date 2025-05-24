from rest_framework import serializers
from .models import BlogPost,User

class BlogPostSerializer(serializers.ModelSerializer):
    profile_image = serializers.URLField(source='userId.profile_image', read_only=True)
    name = serializers.CharField(source='userId.name', read_only=True)
    class Meta:
        model = BlogPost
        fields = ['id','title', 'image', 'content', 'created_at', 'profile_image','name']
