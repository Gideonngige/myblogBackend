from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import BlogPost, Users
import cloudinary.uploader
import pyrebase
import json



config = {
    "apiKey": "AIzaSyDvzmhEaAH7UHCiwchGALP87i2o_-EYAhU",
    "authDomain": "blog-26b72.firebaseapp.com",
    "databaseURL": "https://blog-26b72-default-rtdb.firebaseio.com/",
    "projectId": "blog-26b72",
    "storageBucket": "blog-26b72.firebasestorage.app",
    "messagingSenderId": "578792566453",
   " appId": "1:578792566453:web:7fd8d7912b2feb54bcd8fc",
   " measurementId": "G-LNEKVMY72E"
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth() 
database = firebase.database()

# Create your views here.
def members(request):
    return HttpResponse("Hello world!")

@csrf_exempt
@api_view(['POST'])
def postblog(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')

        if not title or not content or not image:
            return JsonResponse({'error': 'Missing title, content, or image'}, status=400)

        try:
            # Upload image to Cloudinary
            result = cloudinary.uploader.upload(image)
            image_url = result.get('secure_url')

            # Save blog post to database
            blog = BlogPost.objects.create(
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
def get_blog_posts(request):
    try:
        posts = BlogPost.objects.all().order_by('-id')  # Latest posts first
        data = []

        for post in posts:
            data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'image': post.image,
            })

        return JsonResponse({'posts': data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

            if Users.objects.filter(email=email).exists():
                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                return JsonResponse({"message": "Successfully logged in"}, status=200)
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
@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            # Use request.POST and request.FILES for form data and files
            name = request.POST.get("name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            profile_image = request.FILES.get("avatar")

            # Check for missing fields
            if not all([name, email, password, profile_image]):
                return JsonResponse({"message": "Missing required fields"}, status=400)

            # Check if email already exists
            if Users.objects.filter(email=email).exists():
                return JsonResponse({"message": "Email already exists"}, status=400)

            # Create user in Firebase
            user = authe.create_user_with_email_and_password(email, password)
            uid = user['localId']

            # Upload avatar to Cloudinary
            result = cloudinary.uploader.upload(profile_image)
            image_url = result.get('secure_url')

            # Save user in your database
            user = Users(name=name, email=email, profile_image=image_url, password=uid)
            user.save()

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
        return JsonResponse({"message": message})
    except:
        message = "Something went wrong, Please check the email, provided is registered or not"
        return JsonResponse({"message": message})
#start of reset api