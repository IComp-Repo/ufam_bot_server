from rest_framework import serializers
from .models import User, Quiz, Option, Question, Classroom, Professor

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'telegram_id', 'nickname', 'created_at']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'class_instance', 'created_by', 'created_at', 'status', 'start_time', 'end_time', 'questions']
        read_only_fields = ['created_at']

class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'professor', 'created_at']

class ProfessorSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Professor
        fields = ['id', 'user']