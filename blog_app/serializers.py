from rest_framework import serializers
from .models import BlogPost,User, Notification, BlogLikes, Message

class BlogPostSerializer(serializers.ModelSerializer):
    profile_image = serializers.URLField(source='userId.profile_image', read_only=True)
    name = serializers.CharField(source='userId.name', read_only=True)
    likes_count = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = ['id','title', 'image', 'content', 'created_at', 'profile_image','name', 'likes_count']
    def get_likes_count(self, obj):
        return obj.likes.count()

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'is_read']

class MessageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='userId.name', read_only=True)
    class Meta:
        model = Message
        fields = ['name','message', 'created_at']