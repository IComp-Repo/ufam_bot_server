from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ViewSet):
    """
    ViewSet para criar e listar usuários.
    """

    def list(self, request): #GET -> GET ALL
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data) # Return all users

    def create(self, request): #POST -> CREATE USER
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED) # Create a user
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
