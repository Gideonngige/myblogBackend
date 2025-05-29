from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, default='0701000000') 
    ROLES = (
        ('user', 'user'),
        ('admin', 'admin'),
    )
    role = models.CharField(max_length=50,choices=ROLES, default='user')  # 'user' or 'admin'
    password = models.CharField(max_length=200)
    profile_image = models.URLField()

class BlogPost(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', default=1)
    title = models.CharField(max_length=200)
    image = models.URLField()  # Stores Cloudinary URL
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages', default=1)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', default=1)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.userId.name} for {self.product_name}"

class Notification(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', default=1)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.id} for {self.userId.name}"

# accessories/models.py
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('phone', 'Phone'),
        ('earphone', 'Earphone'),
        ('headphone', 'Headphone'),
        ('charger', 'Charger'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductOrder(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='products')
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_orders', default=1)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.userId.name} for {self.product_name}"
