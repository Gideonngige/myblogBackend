# from . auth import verify_firebase_token
from blog_app.models import User
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt

# start of update user profile api
@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
# @verify_firebase_token
def update_user_profile(request):
    try:
        user_id = request.data.get('user_id')
        name = request.data.get('name')
        phone_number = request.data.get('phone_number')
        profile_image = request.FILES.get('profile_image')

        user = User.objects.get(id=user_id)

        if name:
            user.name = name

        if phone_number:
            user.phone_number = phone_number

        if profile_image:
            user.profile_image = profile_image  # ✅ stored locally

        user.save()

        return JsonResponse({
            "message": "Profile updated successfully",
            "profile_image": user.profile_image.url if user.profile_image else None,
            "name": user.name,
            "phone": user.phone_number,
            "email": user.email,
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

    except Exception as e:
        print(e)
        return JsonResponse({
            "message": "Invalid login",
            "error": str(e)
        }, status=400)


# end of update user profile api