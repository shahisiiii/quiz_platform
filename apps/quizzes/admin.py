"""
Django admin configuration for Quizzes app.
"""
from django.contrib import admin
from .models import Category, Quiz, Question, Submission, Answer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model"""
    list_display = ('name', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


class QuestionInline(admin.TabularInline):
    """Inline questions for Quiz admin"""
    model = Question
    extra = 1
    fields = ('question_text', 'correct_answer', 'marks', 'is_active')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin for Quiz model"""
    list_display = ('title', 'category', 'is_active', 'time_limit', 
                    'passing_score', 'created_by', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin for Question model"""
    list_display = ('id', 'quiz', 'question_text_short', 'correct_answer', 
                    'marks', 'is_active')
    list_filter = ('is_active', 'quiz')
    search_fields = ('question_text',)
    ordering = ('quiz', 'id')
    readonly_fields = ('created_at', 'updated_at')
    
    def question_text_short(self, obj):
        """Display shortened question text"""
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


class AnswerInline(admin.TabularInline):
    """Inline answers for Submission admin"""
    model = Answer
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'is_correct', 'marks_obtained')
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin for Submission model"""
    list_display = ('id', 'user', 'quiz', 'score', 'submitted_at')
    list_filter = ('submitted_at', 'quiz')
    search_fields = ('user__username', 'quiz__title')
    ordering = ('-submitted_at',)
    readonly_fields = ('user', 'quiz', 'score', 'total_marks', 
                       'obtained_marks', 'submitted_at')
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin for Answer model"""
    list_display = ('id', 'submission', 'question', 'selected_answer', 
                    'is_correct', 'marks_obtained')
    list_filter = ('is_correct',)
    search_fields = ('submission__user__username', 'question__question_text')
    readonly_fields = ('submission', 'question', 'selected_answer', 
                       'is_correct', 'marks_obtained')