from rest_framework import serializers
from .models import PollUser
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollUser
        fields = ['email', 'password', 'register', 'is_professor']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return PollUser.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class SendPollSerializer(serializers.Serializer):
    chatId = serializers.CharField()
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())

