from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Classroom, Professor, User, Quiz, Question, Tag, Option
from .serializers import ClassroomSerializer, UserSerializer, QuizSerializer, ProfessorSerializer
from django.shortcuts import get_object_or_404

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

class QuizViewSet(viewsets.ModelViewSet):

    def retrieve(self, request, pk=None):
        """
        GET /quizzes/<pk>/
        Retorna um único Quiz pelo seu ID (primary key).
        """
        quiz = get_object_or_404(Quiz, pk=pk)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def list(self, request):
        """
        GET /quizzes/?status=scheduled|opened|closed (opcional)
                    &telegram_id=123 (opcional)
        Retorna uma lista de quizzes
        """
        status_param = request.query_params.get('status')
        telegram_id = request.query_params.get('telegram_id')

        queryset = Quiz.objects.all()

        # 1) Filtrar por status (caso exista)
        if status_param:
            if status_param not in ["scheduled", "opened", "closed"]:
                return Response(
                    {"detail": "Status inválido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(status=status_param)

        # 2) Filtrar por telegram_id
        if telegram_id:
            user = get_object_or_404(User, telegram_id=telegram_id)
            # Exemplo: Filtra quizzes de turmas em que esse user (student) participa
            queryset = queryset.filter(
                class_instance__members__student__user=user
            )

        serializer = QuizSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Exemplo de JSON no POST:
        {
            "title": "Exemplo de Quiz",
            "class_instance": 1,
            "created_by": 2,
            "status": "scheduled",
            "questions": [
                {
                    "text": "Pergunta 1",
                    "tags": ["Django", "Python"],   # Lista de tags
                    "options": [
                        {"text": "Opção A", "is_correct": false},
                        {"text": "Opção B", "is_correct": true}
                    ]
                },
                {
                    "text": "Pergunta 2",
                    "tags": ["Banco de Dados"],
                    "options": [
                        {"text": "Opção C", "is_correct": false},
                        {"text": "Opção D", "is_correct": true}
                    ]
                }
            ]
        }
        """
        data = request.data.copy()
        # Retira "questions" do payload principal
        questions_data = data.pop('questions', [])

        # Valida e cria o Quiz usando o serializer principal
        quiz_serializer = QuizSerializer(data=data)
        quiz_serializer.is_valid(raise_exception=True)
        quiz = quiz_serializer.save()  # cria o Quiz

        # Agora, para cada pergunta no payload, criamos Question, Tag(s) e Option(s)
        for q_data in questions_data:
            tags = q_data.pop('tags', [])       # lista de nomes de tags
            options_data = q_data.pop('options', [])

            # Cria a Question
            question = Question.objects.create(quiz=quiz, **q_data)

            # Trata as tags (cria se não existir, depois adiciona à pergunta)
            for tag_name in tags:
                tag_obj, _created = Tag.objects.get_or_create(name=tag_name)
                question.tags.add(tag_obj)

            # Cria as opções vinculadas à Question
            for opt_data in options_data:
                Option.objects.create(question=question, **opt_data)

        # Re-serializa o quiz completo com perguntas e options
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

        
class ClassroomViewSet(viewsets.ModelViewSet):

    def list(self, request):
        classrooms = Classroom.objects.all()

        serializer = ClassroomSerializer(classrooms, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        classrom = get_object_or_404(Quiz, pk=pk)

        serializer = ClassroomSerializer(classrom)
        return Response(serializer.data)

    def create(self, request):
        serializer = ClassroomSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProfessorViewSet(viewsets.ModelViewSet):

    def list(self, request):
        professors = Professor.objects.all()

        serializer = ProfessorSerializer(professors, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        professor = get_object_or_404(Professor, pk=pk)

        serializer = ProfessorSerializer(professor)
        return Response(serializer.data)

    def create(self, request):
        user_data = request.data.get('user')

        # Verifica se os dados do usuário foram fornecidos
        if not user_data:
            return Response({"error": "User data is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Cria ou obtém o usuário associado
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Cria o Professor associado ao usuário
        professor = Professor.objects.create(user=user)
        professor_serializer = ProfessorSerializer(professor)

        return Response(professor_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        professor = get_object_or_404(Professor, pk=pk)
        professor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)