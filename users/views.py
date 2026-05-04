from django.contrib.auth import login, logout, update_session_auth_hash
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Notification, User
from .serializers import RegisterSerializer, UserSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    _auto_join_world_paddock(user)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


def _auto_join_world_paddock(user):
    from paddocks.models import Paddock, PaddockMembership
    world = Paddock.objects.filter(is_world_paddock=True, is_active=True).first()
    if world and not world.memberships.filter(user=user).exists():
        PaddockMembership.objects.create(paddock=world, user=user, role="member")


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    from django.contrib.auth import authenticate
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    allowed = {k: v for k, v in request.data.items() if k in ("username", "avatar_url")}
    serializer = UserSerializer(request.user, data=allowed, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get("current_password", "")
    new_pw = request.data.get("new_password", "")
    if not request.user.check_password(current):
        return Response({"detail": "Current password is incorrect."}, status=400)
    if len(new_pw) < 8:
        return Response({"detail": "Password must be at least 8 characters."}, status=400)
    request.user.set_password(new_pw)
    request.user.save()
    update_session_auth_hash(request, request.user)
    return Response({"detail": "Password updated."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications(request):
    notes = Notification.objects.filter(user=request.user)[:30]
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({
        "unread": unread,
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notes
        ],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"detail": "Marked all as read."})
