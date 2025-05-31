from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Classroom, Professor, User, Quiz, Question, Tag, Option, Student, Notification
from .serializers import ClassroomSerializer, UserSerializer, DeleteUserSerializer, QuizSerializer, ProfessorSerializer, StudentSerializer, NotificationSerializer
from django.shortcuts import get_object_or_404
from django.db import DatabaseError

class UserViewSet(viewsets.ViewSet):
    """
    ViewSet para criar, listar e buscar usuários.
    """

    def list(self, request):
        try:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            if not users:
                return Response({
                    'success': False,
                    'message': 'Lista de usuários recuperada está vazia.',
                    'data': serializer.data
                } ,status=status.HTTP_404_NOT_FOUND)
            return Response({
                'success': True,
                'message': 'Lista de usuários recuperada com sucesso.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Ocorreu um erro ao listar os usuários.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(user)
            return Response({
                'success': True,
                'message': 'Usuário encontrado com sucesso.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Usuário com ID {pk} não encontrado.',
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    def retrieve_by_telegram(self, request, telegram_id=None):
        try:
            user = get_object_or_404(User, telegram_id=telegram_id)
            serializer = UserSerializer(user)
            return Response({
                'success': True,
                'message': 'Usuário encontrado pelo Telegram ID com sucesso.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Usuário com Telegram ID {telegram_id} não encontrado.',
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Usuário criado com sucesso.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Falha ao criar usuário. Verifique os dados enviados.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erro ao deletar o usuário com ID {pk}.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_by_telegram_id(self, request):
        serializer = DeleteUserSerializer(data=request.data)
        if serializer.is_valid():
            telegram_id = serializer.validated_data.get('telegram_id')
            try:
                user = get_object_or_404(User, telegram_id=telegram_id)
                user.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            except DatabaseError as e_db:
                return Response(
                    {
                        'success': False,
                        'message': f'Falha ao deletar o usuário com Telegram ID {telegram_id}. Verifique o banco de dados.',
                        'error': str(e_db)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )         
            except Exception as e:
                return Response(
                    {
                        'success': False,
                        'message': f'Falha ao deletar o usuário com Telegram ID {telegram_id}. Erro inesperado.', 
                        'error': str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                ) 
        return Response(
            {
                'success': False,
                'message': 'Falha ao deletar usuário. Requisição mal formulada.',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST)


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

class NotificationViewSet(viewsets.ModelViewSet):
    
    def create(self,request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def list(self,request):
        notifications = Notification.objects.all()
        serializer = NotificationSerializer(notifications,many=True)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    def list(self, request):
        try:
            students = Student.objects.all()
            serializer = StudentSerializer(students, many=True)

            if not students:
                return Response(
                    {
                        "success": False,
                        "message": "Lista de estudantes recuperada se encontra vazia.",
                        "data": serializer.data
                    }, 
                    status=status.HTTP_404_NOT_FOUND)

            return Response(
                {
                    'status': True,
                    'message': 'Lista de estudantes recuperada com sucesso.', 
                    'data':serializer.data
                }, 
                status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    'status': False,
                    'message': 'Falha ao recuperar lista de estudantes.', 
                    'error': str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def retrieve(self, request, pk=None):
        try:
            student = get_object_or_404(Student, pk=pk)
            serializer = StudentSerializer(student)
            return Response(
                {
                        'status': True,
                        'message': f'Estudante com PK: {pk} recuperado com sucesso.', 
                        'data':serializer.data
                }, 
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    'status': False,
                    'message': f'Falha ao recuperar estudante com PK: {pk}',
                    'error': str(e) 
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        '''
        Cria-se um registro do model Estudante, junto a criação de um Usuário associado ao mesmo.

        Exemplo de Payload POST: 
        {
            "user": {
                "telegram_id": 6,
                "nickname": "zeromeia"
            },
            "register": 32271010
        }
 
        '''

      
        payload = request.data
        user_serializer = UserSerializer(data=payload.get('user'))
        if not user_serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Falha ao criar usuário. Verifique os dados no campo "user".',
                'errors': user_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student_serializer = StudentSerializer(data=payload)
        if not student_serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Falha ao criar estudante. Verifique os dados de campos como: registro, etc...',
                'errors': student_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = user_serializer.save()
            student_serializer.save(user=user)
            return Response({
                'status': True,
                'message': 'Estudante criado com sucesso.',
                'data': student_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {
                    'status': False,
                    'message': f'Falha ao criar estudante. Erro inesperado.', 
                    'error': str(e) 
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def retrieve_by_register(self, request, register=None):
        try:
            student = get_object_or_404(Student, register=register)
            serializer = StudentSerializer(student)
            return Response({
                'success': True,
                'message': 'Estudante encontrado pelo Número de Matrícula com sucesso.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Estudante com Número de Matrícula {register} não encontrado.',
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            student = get_object_or_404(Student, pk=pk)
            student.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {
                    'status': False,
                    'message': f'Falha ao deletar estudante com PK: {pk}',
                    'error': str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                


