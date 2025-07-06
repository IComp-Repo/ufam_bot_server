from rest_framework import serializers
from .models import PollUser, Group
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollUser
        fields = ['email', 'password', 'register', 'telegram_id', 'is_professor']
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
    options = serializers.ListField(
        child=serializers.CharField(), min_length=2, max_length=10
    )
    correctOption = serializers.IntegerField(required=False, min_value=0)


class SingleQuizSerializer(serializers.Serializer):
    question = serializers.CharField()
    options = serializers.ListField(
        child=serializers.CharField(), min_length=2, max_length=10
    )
    correctOption = serializers.IntegerField(min_value=0)


class SendQuizSerializer(serializers.Serializer):
    chatId = serializers.CharField()
    questions = serializers.ListField()
    schedule_date = serializers.DateField(required=False)
    schedule_time = serializers.TimeField(required=False)

class BindGroupSerializer(serializers.Serializer):
    telegram_id = serializers.CharField()
    chat_id = serializers.CharField()
    chat_title = serializers.CharField()

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'chat_id', 'fetch_date']
