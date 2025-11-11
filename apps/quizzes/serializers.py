"""
Serializers for quiz-related operations.
Includes nested serializers for complex quiz submission logic.
"""
from rest_framework import serializers
from .models import Category, Quiz, Question, Submission, Answer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    created_by = serializers.StringRelatedField(read_only=True)
    quiz_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'is_active', 
                  'created_by', 'quiz_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def get_quiz_count(self, obj):
        """Return count of active quizzes in this category"""
        return obj.quizzes.filter(is_active=True).count()


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model (Admin view with correct answer)"""
    
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'option_a', 'option_b', 
                  'option_c', 'option_d', 'correct_answer', 'marks', 
                  'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Serializer for Question model (User view without correct answer)"""
    
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'option_a', 'option_b', 
                  'option_c', 'option_d', 'marks')


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for Quiz model with nested questions"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'category', 'category_name',
                  'time_limit', 'passing_score', 'is_active', 'created_by',
                  'questions', 'question_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def get_question_count(self, obj):
        """Return count of active questions"""
        return obj.questions.filter(is_active=True).count()


class QuizListSerializer(serializers.ModelSerializer):
    """Simplified serializer for quiz listing (without questions)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'category', 'category_name',
                  'time_limit', 'passing_score', 'question_count', 'created_at')
    
    def get_question_count(self, obj):
        return obj.questions.filter(is_active=True).count()


class QuizPublicSerializer(serializers.ModelSerializer):
    """Serializer for quiz detail (users - without correct answers)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    questions = QuestionPublicSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'category_name', 
                  'time_limit', 'passing_score', 'questions', 'question_count')
    
    def get_question_count(self, obj):
        return obj.questions.filter(is_active=True).count()


class AnswerSubmissionSerializer(serializers.Serializer):
    """Serializer for individual answer submission"""
    question_id = serializers.IntegerField()
    selected_answer = serializers.ChoiceField(choices=['A', 'B', 'C', 'D'])
    
    def validate_question_id(self, value):
        """Validate that question exists"""
        if not Question.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive question ID")
        return value


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for complete quiz submission"""
    quiz_id = serializers.IntegerField()
    answers = AnswerSubmissionSerializer(many=True)
    
    def validate_quiz_id(self, value):
        """Validate that quiz exists and is active"""
        if not Quiz.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive quiz ID")
        return value
    
    def validate_answers(self, value):
        """Ensure answers are provided"""
        if not value:
            raise serializers.ValidationError("At least one answer is required")
        return value


class AnswerDetailSerializer(serializers.ModelSerializer):
    """Serializer for answer details in submission"""
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)
    
    class Meta:
        model = Answer
        fields = ('question_text', 'selected_answer', 'correct_answer', 
                  'is_correct', 'marks_obtained')


class SubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submission with detailed results"""
    user = serializers.StringRelatedField(read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    answers = AnswerDetailSerializer(many=True, read_only=True)
    passed = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = ('id', 'user', 'quiz_title', 'submitted_at', 'score',
                  'total_marks', 'obtained_marks', 'passed', 'answers')
        read_only_fields = ('id', 'submitted_at')
    
    def get_passed(self, obj):
        """Check if user passed based on quiz passing score"""
        return obj.score >= obj.quiz.passing_score


class SubmissionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for submission listing"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    passed = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = ('id', 'user_username', 'user_email', 'quiz_title', 
                  'submitted_at', 'score', 'total_marks', 'obtained_marks', 'passed')
    
    def get_passed(self, obj):
        return obj.score >= obj.quiz.passing_score