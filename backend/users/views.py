from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer, 
    UserLoginSerializer,
    ChangePasswordSerializer
)

def get_token_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class AuthViewSet(GenericViewSet):
    @action(detail=False, methods=['post'], permissions_classes=[permissions.AllowAny])
    def register(self, request):
        serialzer = UserRegistrationSerializer(data=request.data)
        if serialzer.is_valid():
            user = serialzer.save()
            tokens = get_token_for_user(user)

            return Response({
                'user': UserProfileSerializer(user.data),
                'tokens': tokens,
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serialzer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permissions_classes = [permissions.AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_token_for_user(user)
            return Response({
                'user': UserProfileSerializer(user.data),
                'tokens': tokens,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    