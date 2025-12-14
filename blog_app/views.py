from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import BlogPost, User, Message, Order, Notification, Product, ProductOrder, BlogLikes
import cloudinary.uploader
import pyrebase
import json
from .serializers import BlogPostSerializer, NotificationSerializer, MessageSerializer
from rest_framework.response import Response
from django.db.models import Sum
import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

import firebase_admin
from firebase_admin import credentials, auth
import os, json
from django.http import JsonResponse

import logging
logger = logging.getLogger("backend")



firebaseConfig = {
  "apiKey": os.environ.get("FIREBASE_API_KEY"),
  "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
  "databaseURL": os.environ.get("FIREBASE_DATABASE_URL"),
  "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
  "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
  "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
  "appId": os.environ.get("FIREBASE_APP_ID"),
  "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID")
};

firebase = pyrebase.initialize_app(firebaseConfig)
authe = firebase.auth() 
database = firebase.database()

# Initialize Firebase once (e.g., in settings.py or a startup file)
service_account_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
# cred = credentials.Certificate("serviceAccountKey.json")
cred = credentials.Certificate(service_account_info)
# firebase_admin.initialize_app(cred)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# verify apis access
def verify_firebase_token(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Authorization header missing"}, status=401)

        try:
            token = auth_header.split(" ")[1]  # "Bearer <token>"
            decoded = auth.verify_id_token(token)
            request.firebase_uid = decoded["uid"]   # <===== IMPORTANT
        except Exception as e:
            return JsonResponse({"error": "Invalid token", "details": str(e)}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper


# Create your views here.
def index(request):
    return render(request, 'index.html')

@csrf_exempt
@api_view(['POST'])
def postblog(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        user_id = request.POST.get('user_id')

        user = User.objects.filter(id=user_id).first()

        if not title or not content or not image:
            return JsonResponse({'error': 'Missing title, content, or image'}, status=400)

        try:
            # Upload image to Cloudinary
            result = cloudinary.uploader.upload(image)
            image_url = result.get('secure_url')

            # Save blog post to database
            
            blog = BlogPost.objects.create(
                userId=user,  # use ForeignKey to User model
                title=title,
                image=image_url,  # use URLField in your model
                content=content,
            )

            return JsonResponse({
                'message': 'Blog post created successfully',
                'post': {
                    'id': blog.id,
                    'title': blog.title,
                    'content': blog.content,
                    'image': blog.image
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)


@csrf_exempt
@api_view(['GET'])
# @verify_firebase_token
def get_blog_posts(request):
    try:
        posts = BlogPost.objects.all().order_by('-id')
        serializer = BlogPostSerializer(posts, many=True)
        return Response({'posts': serializer.data}, status=200)

    except Exception as e:
        return Response({'error': str(e)}, status=500)

# get single blog post
@csrf_exempt
@api_view(['GET'])
def get_blog_post(request, post_id):
    try:
        post = BlogPost.objects.get(id=post_id)
        serializer = BlogPostSerializer(post)
        return Response({'post': serializer.data}, status=200)

    except BlogPost.DoesNotExist:
        return Response({'error': 'Blog post not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

#start of signin api
@csrf_exempt
@api_view(['POST'])
def signin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse({"message": "Email and password are required"}, status=400)

            user = authe.sign_in_with_email_and_password(email, password)
            
            if User.objects.filter(email=email).exists():
                # log user
                logger.info(f"User sign in: Email: {email}")

                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                get_user = User.objects.filter(email=email).first()
                user_id = get_user.id
                profile_image = get_user.profile_image
                name = get_user.name
                email = get_user.email
                role = get_user.role
                return JsonResponse(
                    {
                        "message": "Successfully logged in", 
                        "user_id":user_id,
                        "profile_image": profile_image,
                        "name": name,
                        "email": email,
                        "phone_number": get_user.phone_number,
                        "is_verified": get_user.is_verified,
                        "role": role,
                        "token": session_id
                    }, status=200)
            else:
                return JsonResponse({"message": "No user found with this email, please register"}, status=404)

        except Exception as e:
            print("Error:", str(e))  # Optional logging
            return JsonResponse({"message": "Invalid credentials. Please check your email and password."}, status=401)

    return JsonResponse({"message": "Invalid request method"}, status=405)
#end of signin api

#start of logout api
def logout(request):
    try:
        del request.session['uid']
    except:
        pass 
    return JsonResponse({"message": "Successfully logged out"})
#end of logout api

#start of register api
@csrf_exempt
@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        try:
            # Use request.POST and request.FILES for form data and files
            name = request.POST.get("name")
            phone_number = request.POST.get("phonenumber")
            email = request.POST.get("email")
            password = request.POST.get("password")
            profile_image = request.FILES.get("avatar")

            # Check for missing fields
            if not all([name, email, password, profile_image]):
                return JsonResponse({"message": "Missing required fields"}, status=400)

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({"message": "Email already exists"}, status=400)

            # Create user in Firebase
            user = authe.create_user_with_email_and_password(email, password)
            uid = user['localId']

            # Upload avatar to Cloudinary
            result = cloudinary.uploader.upload(profile_image)
            image_url = result.get('secure_url')

            # Save user in your database
            user = User(name=name, email=email, phone_number=phone_number, profile_image=image_url, password=uid)
            user.save()
            
            user2 = User.objects.filter(email=email).first()
            notification = Notification.objects.create(
                userId=user2,
                message="Welcome to G-Tech Company! Your account has been created successfully. Read, post blogs and buy your favourite accessories.",
                is_read=False
            )

            # send_mail(
            #     subject='Welcome to G-Blog!',
            #     message='Your account has been created successfully.',
            #     from_email=settings.EMAIL_HOST_USER,
            #     recipient_list=[email],
            #     fail_silently=False,
            # )
            logger.info(f"User sign up: Email: {email}, Name: {name}")

            return JsonResponse({"message": "Successfully signed up"}, status=201)

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"message": "Signup failed", "error": str(e)}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=405)
#end of register api

#end of reset api
def resetpassword(request, email):
    try:
        authe.send_password_reset_email(email)
        message = "A email to reset password is successfully sent"
        logger.info(f"Email reset link sent to: {email}")
        return JsonResponse({"message": message})
    except:
        message = "Something went wrong, Please check the email, provided is registered or not"
        logger.info(f"Failed to send reset password email to: {email}")
        return JsonResponse({"message": message})
#start of reset api

# start of send message api
@csrf_exempt
@api_view(['POST'])
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            message = data.get("message")

            if not user_id or not message:
                return JsonResponse({"message": "User ID and message are required"}, status=400)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({"message": "User not found"}, status=404)

            # Save the message to the database
            new_message = Message.objects.create(userId=user, message=message)

            logger.info(f"Message sent by {user.name}: {message}")

            return JsonResponse({"message": "Message sent successfully", "message_id": new_message.id}, status=200)

        except Exception as e:
            print("Error:", str(e))
            logger.info(f"Error sending message: {str(e)}")
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)
# end of send message api

# start of order service api
@csrf_exempt
@api_view(['POST'])
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            product_name = data.get("product_name")
            quantity = data.get("quantity")
            price = data.get("price")
            print("About to create notification...")

            if not all([user_id, product_name, quantity, price]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({"message": "User not found"}, status=404)

            # Create the order
            order = Order.objects.create(
                userId=user,
                product_name=product_name,
                quantity=quantity,
                price=price
            )
            print("Order created successfully, creating notification...")
            notification = Notification.objects.create(
                userId=user,
                message=f"Your order for {product_name} has been received successfully.",
                is_read=False
            )
            
            # log user here
            logger.info(f"Order created for {user.name}: {product_name}")
            return JsonResponse({"message": "Order created successfully", "order_id": order.id}, status=200)

        except Exception as e:
            print("Error:", str(e))
            logger.info(f"Error creating order: {str(e)}")
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)
# end of order service api

# start of get notifications api
@api_view(['GET'])
def get_user_notifications(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        notifications = Notification.objects.filter(userId=user, is_read=False).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        # log here
        logger.info(f"User notifications fetched: {user.name} {user.email}")

        return Response(serializer.data)
    except User.DoesNotExist:
        # log user here
        logger.info(f"User not found: {user_id}")
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            description = request.POST.get("description")
            category = request.POST.get("category")
            price = request.POST.get("price")
            stock = request.POST.get("stock")
            image = request.FILES.get("image")

            if not all([name, category, price, stock, image]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            # Create the product
            result = cloudinary.uploader.upload(image)
            image_url = result.get('secure_url')

            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                stock=stock,
                image=image_url,
            )
            logger.info(f"Product added: {name}")
            return JsonResponse({"message": "Product added successfully", "product_id": product.id}, status=201)

        except Exception as e:
            print("Error:", str(e))
            logger.info(f"Error adding product: {str(e)}")
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)


def get_products(request):
    try:
        products = Product.objects.all()
        product_list = []
        for product in products:
            product_list.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': product.category,
                'price': str(product.price),
                'stock': product.stock,
                'image': product.image,
            })
        # log here
        logger.info("Products fetched successfully")

        return JsonResponse({"products": product_list}, status=200)
    except Exception as e:
        print("Error:", str(e))
        logger.info(f"Error fetching products: {str(e)}")
        return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
def add_stock(request, product_id, additional_stock):
    try:
        product = Product.objects.get(id=product_id)
        if additional_stock < 0:
            return JsonResponse({"message": "Stock cannot be negative"}, status=400)

        product.stock += additional_stock
        product.save()

        logger.info(f"Stock updated for product {product_id}: {additional_stock}")

        return JsonResponse({"message": "Stock updated successfully", "new_stock": product.stock}, status=200)

    except Product.DoesNotExist:
        logger.info(f"Product not found: {product_id}")
        return JsonResponse({"message": "Product not found"}, status=404)
    except Exception as e:
        print("Error:", str(e))
        logger.info(f"Error updating stock: {str(e)}")
        return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

# start of order products api
@csrf_exempt
@api_view(['POST'])
def create_product_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            user_id = data.get("user_id")
            product_name = data.get("product_name")
            quantity = data.get("quantity")
            price = data.get("price")
            print("About to create notification...")
            print("Data received:", data)

            if not all([user_id, product_name, quantity, price]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({"message": "User not found"}, status=404)
            
            product = Product.objects.filter(id=product_id).first()
            if quantity > product.stock:
                return JsonResponse({"message":"Your order is more that our stock!!"})
            # Create the order
            order = ProductOrder.objects.create(
                product_id=product,
                userId=user,
                product_name=product_name,
                quantity=quantity,
                price=price,
                delivered=False
            )
            product.stock -= quantity
            product.save()
            print("Order created successfully, creating notification...")

            logger.info(f"Order created for {user.name}: {product_name}")

            notification = Notification.objects.create(
                userId=user,
                message=f"Your order for {product_name} has been received successfully.It will be delivered soon.",
                is_read=False
            )
            

            return JsonResponse({"message": "Order created successfully", "order_id": order.id}, status=200)

        except Exception as e:
            print("Error:", str(e))

            logger.info(f"Error creating order: {str(e)}")

            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)
# end of order products api

# create bulky order api
@csrf_exempt
@api_view(['POST'])
def create_bulk_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            products = data.get("products", [])  # List of items

            if not user_id or not products:
                return JsonResponse({"message": "User ID and product list are required"}, status=400)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({"message": "User not found"}, status=404)

            order_ids = []
            for item in products:
                product_id = item.get("product_id")
                product_name = item.get("product_name")
                quantity = item.get("quantity")
                price = item.get("price")

                # Check required fields
                if not all([product_id, product_name, quantity, price]):
                    return JsonResponse({"message": "Missing product details in one of the items"}, status=400)

                product = Product.objects.filter(id=product_id).first()
                if not product:
                    return JsonResponse({"message": f"Product with ID {product_id} not found"}, status=404)

                if quantity > product.stock:
                    return JsonResponse({"message": f"Not enough stock for {product.name}"}, status=400)

                # Create order
                order = ProductOrder.objects.create(
                    product_id=product,
                    userId=user,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    delivered=False
                )
                product.stock -= quantity
                product.save()
                order_ids.append(order.id)

                # log user here
                logger.info(f"Order created for {user.name}: {product_name}")

                # Notification for each item
                Notification.objects.create(
                    userId=user,
                    message=f"Order for {product_name} placed successfully. We’ll deliver soon.",
                    is_read=False
                )

            return JsonResponse({"message": "All orders created successfully", "order_ids": order_ids}, status=200)

        except Exception as e:
            print("Error:", str(e))
            logger.info(f"Error creating orders: {str(e)}")
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

# endof create bulky order api


# start of get product orders api
@api_view(['GET'])
def get_product_orders(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        product_orders = ProductOrder.objects.filter(userId=user, delivered=False).order_by('-created_at')
        orders_data = []
        for order in product_orders:
            orders_data.append({
                'id': order.id,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'price': str(order.price),
                'delivered': order.delivered,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        # log user here
        logger.info(f"User orders fetched: {user.name} {user.email}")

        return Response({'orders': orders_data}, status=200)
    except User.DoesNotExist:
        # log user here
        logger.info(f"User not found: {user_id}")

        return Response({'error': 'User not found'}, status=404)
# end of get product orders api

# start of get all orders api
@api_view(['GET'])
def get_all_orders(request):
    try:
        orders = ProductOrder.objects.filter(delivered=False).order_by('-created_at')
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'price': str(order.price),
                'delivered': order.delivered,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': order.userId.id,
                'user_name': order.userId.name
            })
        # log user here
        logger.info("All orders fetched")

        return Response({'orders': orders_data}, status=200)
    except Exception as e:
        print("Error:", str(e))
        logger.info(f"Error fetching orders: {str(e)}")
        return Response({'error': str(e)}, status=500)
# end of get all orders api

# start of confirm order api
@api_view(['GET'])
def confirm_order(request, order_id):
    try:
        order = ProductOrder.objects.get(id=order_id)
        order.delivered = True
        order.save()

        # Create a notification for the user
        notification = Notification.objects.create(
            userId=order.userId,
            message=f"Your order for {order.product_name} has been delivered successfully.",
            is_read=False
        )
        # log user here
        logger.info(f"Order delivered: {order.product_name} by: {order.userId.name}")

        return Response({'message': 'Order confirmed successfully'}, status=200)
    except ProductOrder.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
# end of confirm order api

# start of likes api
@api_view(['GET'])
def like_blog_post(request,user_id, blog_id):
    try:
        blog_id = BlogPost.objects.filter(id=blog_id).first()
        user_id = User.objects.filter(id=user_id).first()
        blog_likes = BlogLikes.objects.filter(userId=user_id, blog_id=blog_id).first()
        if blog_likes:
            total_likes = BlogLikes.objects.filter(blog_id=blog_id).count() or 0
            return Response({'message': 'You have already liked this blog post', 'likes': total_likes}, status=200)
        else:
            blog_likes = BlogLikes.objects.create(userId=user_id, blog_id=blog_id, likes=1)
            # count total likes
            total_likes = BlogLikes.objects.filter(blog_id=blog_id).count() or 0
        return Response({'message': 'Blog post liked successfully', 'likes': total_likes}, status=200)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Blog post not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
# end of likes api

# mark notifications as read
@api_view(['GET'])
def mark_notification_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'}, status=200)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
# end of mark notifications as read api

# get dashboard data
@api_view(['GET'])
def get_dashboard_data(request):
    try:
        total_users = User.objects.count()
        total_blog_posts = BlogPost.objects.count()
        total_orders = ProductOrder.objects.count()
        total_products = Product.objects.count()
        total_messages = Message.objects.count()
        total_notifications = Notification.objects.filter(is_read=False).count()
        # get daily sales
        daily_sales = ProductOrder.objects.filter(created_at__date=datetime.date.today()).aggregate(Sum('price'))['price__sum'] or 0
        # get weekly sales
        weekly_sales = ProductOrder.objects.filter(created_at__date__gte=datetime.date.today() - datetime.timedelta(days=7)).aggregate(Sum('price'))['price__sum'] or 0
        # get monthly sales
        monthly_sales = ProductOrder.objects.filter(created_at__date__gte=datetime.date.today() - datetime.timedelta(days=30)).aggregate(Sum('price'))['price__sum'] or 0
        # get yearly sales
        yearly_sales = ProductOrder.objects.filter(created_at__date__gte=datetime.date.today() - datetime.timedelta(days=365)).aggregate(Sum('price'))['price__sum'] or 0

        data = {
            'total_users': total_users,
            'total_blog_posts': total_blog_posts,
            'total_orders': total_orders,
            'total_messages':total_messages,
            'total_products': total_products,
            'total_notifications': total_notifications,
            'daily_sales': str(daily_sales),
            'weekly_sales': str(weekly_sales),
            'monthly_sales': str(monthly_sales),
            'yearly_sales': str(yearly_sales),
            
        }

        return Response(data, status=200)

    except Exception as e:
        return Response({'error': str(e)}, status=500)
# end of get dashboard data api

# send email api
@api_view(['GET'])
def send_latest_blog_email(request):
    latest_blog = BlogPost.objects.order_by('-created_at').first()

    if not latest_blog:
        return Response({"error": "No blog posts found."}, status=404)

    # Generate the email body using an HTML template
    html_content = render_to_string('email_blog.html', {
        'title': latest_blog.title,
        'content': latest_blog.content,
        'image_url': latest_blog.image
    })

    email = EmailMessage(
        subject=f"Latest Blog: {latest_blog.title}",
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=['gideonushindi94@gmail.com']
    )
    email.content_subtype = 'html'  # Important for HTML content
    email.send(fail_silently=False)

    return Response({"message": "Blog email sent successfully."})


# start of get notifications api
@api_view(['GET'])
def get_messages(request):
    try:
        messages = Message.objects.all().order_by('-created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
