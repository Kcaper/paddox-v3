from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import RegisterSerializer, UserSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)
