"""
ViewSets for quiz management using ModelViewSet.
Includes Redis caching for improved performance.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Q

from apps.users.permissions import IsAdminUser
from .models import Category, Quiz, Question, Submission, Answer
from .serializers import (
    CategorySerializer,
    QuizSerializer,
    QuizListSerializer,
    QuizPublicSerializer,
    QuestionSerializer,
    QuizSubmissionSerializer,
    SubmissionSerializer,
    SubmissionListSerializer
)
from .utils import create_submission, validate_quiz_questions, invalidate_quiz_cache, generate_quiz_statistics


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations.
    Only admins can create/update/delete categories.
    All authenticated users can view active categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        """Admin-only for create/update/delete, authenticated for read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter categories based on user role.
        Admins see all, users see only active categories.
        Cached for performance.
        """
        user = self.request.user
        
        if user.is_staff:
            return Category.objects.all().order_by('name')
        
        # Cache active categories for normal users
        cache_key = 'active_categories'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(Category.objects.filter(
                is_active=True
            ).order_by('name'))
            cache.set(cache_key, categories, timeout=600)  # 10 minutes
        
        return categories
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
        cache.delete('active_categories')
    
    def perform_update(self, serializer):
        """Invalidate cache on update"""
        serializer.save()
        cache.delete('active_categories')
    
    def perform_destroy(self, instance):
        """Invalidate cache on delete"""
        instance.delete()
        cache.delete('active_categories')


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quiz CRUD operations.
    - Admins: Full CRUD access with all quiz details
    - Users: Read-only access to active quizzes (without correct answers)
    """
    serializer_class = QuizSerializer
    
    def get_permissions(self):
        """Admin-only for create/update/delete, authenticated for read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 
                           'add_question', 'update_question', 'delete_question']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Return queryset based on user role.
        Optimized with select_related and prefetch_related.
        """
        queryset = Quiz.objects.select_related('category', 'created_by')
        
        if self.request.user.is_staff:
            # Admins see all quizzes
            return queryset.prefetch_related('questions').order_by('-created_at')
        else:
            # Users only see active quizzes with active questions
            return queryset.filter(is_active=True).prefetch_related(
                Prefetch(
                    'questions',
                    queryset=Question.objects.filter(is_active=True)
                )
            ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role"""
        if self.action == 'list':
            return QuizListSerializer
        
        if self.action == 'retrieve' and not self.request.user.is_staff:
            return QuizPublicSerializer
        
        return QuizSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List quizzes with caching for normal users.
        """
        user = request.user
        
        # Cache for normal users only
        if not user.is_staff:
            cache_key = 'quiz_list_active'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            cache.set(cache_key, serializer.data, timeout=300)  # 5 minutes
            return Response(serializer.data)
        
        return super().list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
        cache.delete('quiz_list_active')
    
    def perform_update(self, serializer):
        """Invalidate cache on update"""
        instance = serializer.save()
        invalidate_quiz_cache(instance.id)
    
    def perform_destroy(self, instance):
        """Invalidate cache on delete"""
        quiz_id = instance.id
        instance.delete()
        invalidate_quiz_cache(quiz_id)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_question(self, request, pk=None):
        """
        Add a question to the quiz.
        
        Body: {
            "question_text": "string",
            "option_a": "string",
            "option_b": "string",
            "option_c": "string",
            "option_d": "string",
            "correct_answer": "A" | "B" | "C" | "D",
            "marks": integer,
            "is_active": boolean (optional)
        }
        """
        quiz = self.get_object()
        serializer = QuestionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(quiz=quiz)
            invalidate_quiz_cache(quiz.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request, pk=None):
        """
        Get quiz statistics (admin only).
        Calculates stats synchronously without caching.
        """
        quiz = self.get_object()
        
        # Call the function to calculate stats
        stats = generate_quiz_statistics(quiz.id)
        
        return Response(stats, status=status.HTTP_200_OK)
        


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Question management (Admin only).
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Optimize queryset with select_related"""
        return Question.objects.select_related('quiz').order_by('quiz', 'id')
    
    def perform_update(self, serializer):
        """Invalidate quiz cache when question is updated"""
        instance = serializer.save()
        invalidate_quiz_cache(instance.quiz.id)
    
    def perform_destroy(self, instance):
        """Invalidate quiz cache when question is deleted"""
        quiz_id = instance.quiz.id
        instance.delete()
        invalidate_quiz_cache(quiz_id)


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quiz submissions.
    - Users: Can submit answers and view their own submissions
    - Admins: Can view all submissions
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']  # Only allow GET and POST
    
    def get_queryset(self):
        """
        Filter submissions based on user role.
        Optimized with select_related and prefetch_related.
        """
        user = self.request.user
        queryset = Submission.objects.select_related('user', 'quiz').prefetch_related(
            'answers__question'
        )
        
        if user.is_staff:
            # Admins see all submissions
            return queryset.order_by('-submitted_at')
        else:
            # Users only see their own submissions
            return queryset.filter(user=user).order_by('-submitted_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SubmissionListSerializer
        elif self.action == 'create':
            return QuizSubmissionSerializer
        return SubmissionSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List submissions with caching.
        """
        user = request.user
        
        # Cache user's own submissions
        if not user.is_staff:
            cache_key = f'user_submissions_{user.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            cache.set(cache_key, serializer.data, timeout=300)  # 5 minutes
            return Response(serializer.data)
        
        return super().list(request, *args, **kwargs)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Submit quiz answers.
        
        Body: {
            "quiz_id": integer,
            "answers": [
                {"question_id": integer, "selected_answer": "A|B|C|D"},
                ...
            ]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quiz_id = serializer.validated_data['quiz_id']
        answers_data = serializer.validated_data['answers']
        
        try:
            quiz = Quiz.objects.get(id=quiz_id, is_active=True)
        except Quiz.DoesNotExist:
            return Response({
                'error': 'Quiz not found or is inactive'
            }, status=status.HTTP_404_NOT_FOUND)
            
        question_ids = []

        for answer_item in answers_data:
            question_ids.append(answer_item["question_id"])

        existing_answers = Answer.objects.filter(
            submission__user=request.user,
            question_id__in=question_ids
        ).values_list('question_id', flat=True)

        if existing_answers:
            return Response({
                'error': f'You have already submitted answers for these questions: {list(existing_answers)}'
            }, status=status.HTTP_400_BAD_REQUEST)
  
        # Validate quiz has questions
        is_valid, error_msg = validate_quiz_questions(quiz)
        if not is_valid:
            return Response({
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create submission with answers
        submission = create_submission(request.user, quiz, answers_data)
        
        # Return detailed submission
        response_serializer = SubmissionSerializer(submission)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_submissions(self, request):
        """Get current user's submissions"""
        submissions = self.get_queryset().filter(user=request.user)
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)
    
