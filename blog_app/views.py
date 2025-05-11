from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from .models import BlogPost
import cloudinary.uploader


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