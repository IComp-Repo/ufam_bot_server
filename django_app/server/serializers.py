from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    PollUser,
    Group,
    PollUserGroup
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = PollUser
        fields = ['email', 'password', 'name']

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
    telegram_id = serializers.IntegerField()
    chat_id = serializers.IntegerField()
    chat_title = serializers.CharField()

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'chat_id', 'fetch_date']

class UserGroupListItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='group.id', read_only=True)
    title = serializers.CharField(source='group.title', read_only=True)
    chat_id = serializers.IntegerField(source='group.chat_id', read_only=True)
    fetch_date = serializers.DateTimeField(source='group.fetch_date', read_only=True)

    class Meta:
        model = PollUserGroup
        fields = ['id', 'title', 'chat_id', 'fetch_date', 'bind_date']
