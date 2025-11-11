"""
Models for quiz platform: Categories, Quizzes, Questions, and Submissions.
Includes proper indexing for PostgreSQL performance optimization.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """
    Quiz categories created by admin.
    Examples: Science, History, Mathematics, etc.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='categories'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='cat_name_idx'),
            models.Index(fields=['is_active'], name='cat_active_idx'),
            models.Index(fields=['-created_at'], name='cat_created_idx'),
        ]
    
    def __str__(self):
        return self.name


class Quiz(models.Model):
    """
    Quiz created by admin, associated with a category.
    Can be activated/deactivated.
    """
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    time_limit = models.IntegerField(
        help_text="Time limit in minutes",
        validators=[MinValueValidator(1)],
        default=30
    )
    passing_score = models.IntegerField(
        help_text="Minimum score to pass (percentage)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=60
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_quizzes'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title'], name='quiz_title_idx'),
            models.Index(fields=['is_active'], name='quiz_active_idx'),
            models.Index(fields=['category', 'is_active'], name='quiz_cat_active_idx'),
            models.Index(fields=['-created_at'], name='quiz_created_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def total_questions(self):
        """Return total number of active questions in this quiz"""
        return self.questions.filter(is_active=True).count()


class Question(models.Model):
    """
    Question belonging to a quiz with 4 options.
    One option is marked as correct.
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'Option A'), ('B', 'Option B'), 
                 ('C', 'Option C'), ('D', 'Option D')]
    )
    marks = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'questions'
        ordering = ['id']
        indexes = [
            models.Index(fields=['quiz', 'is_active'], name='ques_quiz_active_idx'),
            models.Index(fields=['is_active'], name='ques_active_idx'),
        ]
    
    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}"


class Submission(models.Model):
    """
    User's quiz submission with answers and calculated score.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage score"
    )
    total_marks = models.IntegerField()
    obtained_marks = models.IntegerField()
    
    class Meta:
        db_table = 'submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', '-submitted_at'], name='sub_user_date_idx'),
            models.Index(fields=['quiz', '-submitted_at'], name='sub_quiz_date_idx'),
            models.Index(fields=['-submitted_at'], name='sub_date_idx'),
            models.Index(fields=['user', 'quiz'], name='sub_user_quiz_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"


class Answer(models.Model):
    """
    Individual answer for each question in a submission.
    """
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    selected_answer = models.CharField(
        max_length=1,
        choices=[('A', 'Option A'), ('B', 'Option B'), 
                 ('C', 'Option C'), ('D', 'Option D')]
    )
    is_correct = models.BooleanField()
    marks_obtained = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'answers'
        unique_together = ['submission', 'question']
        indexes = [
            models.Index(fields=['submission'], name='ans_submission_idx'),
            models.Index(fields=['question'], name='ans_question_idx'),
        ]
    
    def __str__(self):
        return f"Answer to Q{self.question.id} - {'Correct' if self.is_correct else 'Wrong'}"