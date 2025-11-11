"""
Utility functions for quiz operations.
Includes score calculation and validation helpers.
"""
from django.core.cache import cache
from .models import Quiz, Question, Submission, Answer
from django.db.models import Avg, Count, Q, F, Min, Max


def calculate_quiz_score(quiz, answers_data):
    """
    Calculate score for a quiz submission.
    
    Args:
        quiz: Quiz instance
        answers_data: List of dicts with 'question_id' and 'selected_answer'
    
    Returns:
        dict: {
            'total_marks': int,
            'obtained_marks': int,
            'score': float (percentage),
            'answer_details': list
        }
    """
    # Get all active questions for this quiz
    questions = Question.objects.filter(
        quiz=quiz,
        is_active=True
    ).select_related('quiz')
    
    # Create a map of question_id -> Question object
    question_map = {q.id: q for q in questions}
    
    # Initialize counters
    total_marks = sum(q.marks for q in questions)
    obtained_marks = 0
    answer_details = []
    
    # Process each answer
    for answer_data in answers_data:
        question_id = answer_data['question_id']
        selected_answer = answer_data['selected_answer']
        
        # Skip if question not found or not in this quiz
        if question_id not in question_map:
            continue
        
        question = question_map[question_id]
        
        # Check if answer is correct
        is_correct = (selected_answer == question.correct_answer)
        marks_obtained = question.marks if is_correct else 0
        obtained_marks += marks_obtained
        
        answer_details.append({
            'question': question,
            'selected_answer': selected_answer,
            'is_correct': is_correct,
            'marks_obtained': marks_obtained
        })
    
    # Calculate percentage score
    score = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
    
    return {
        'total_marks': total_marks,
        'obtained_marks': obtained_marks,
        'score': round(score, 2),
        'answer_details': answer_details
    }


def create_submission(user, quiz, answers_data):
    """
    Create a quiz submission with answers.
    
    Args:
        user: User instance
        quiz: Quiz instance
        answers_data: List of answer dictionaries
    
    Returns:
        Submission instance
    """
    # Calculate score
    score_data = calculate_quiz_score(quiz, answers_data)
    
    # Create submission
    submission = Submission.objects.create(
        user=user,
        quiz=quiz,
        score=score_data['score'],
        total_marks=score_data['total_marks'],
        obtained_marks=score_data['obtained_marks']
    )
    
    # Create answer records
    Answer.objects.bulk_create([
        Answer(
            submission=submission,
            question=detail['question'],
            selected_answer=detail['selected_answer'],
            is_correct=detail['is_correct'],
            marks_obtained=detail['marks_obtained']
        )
        for detail in score_data['answer_details']
    ])
    
    # Invalidate relevant caches
    cache_keys = [
        f'user_submissions_{user.id}',
        f'quiz_submissions_{quiz.id}',
        f'user_report_{user.id}',  # Invalidate user report cache
        f'quiz_stats_{quiz.id}',   # Invalidate quiz stats cache
    ]
    cache.delete_many(cache_keys)
    
    return submission


def validate_quiz_questions(quiz):
    """
    Validate that a quiz has at least one active question.
    
    Args:
        quiz: Quiz instance
    
    Returns:
        tuple: (is_valid, error_message)
    """
    active_questions = quiz.questions.filter(is_active=True).count()
    
    if active_questions == 0:
        return False, "Quiz must have at least one active question"
    
    return True, None


def get_cached_quiz(quiz_id):
    """
    Get quiz from cache or database.
    
    Args:
        quiz_id: Quiz ID
    
    Returns:
        Quiz instance or None
    """
    cache_key = f'quiz_{quiz_id}'
    quiz = cache.get(cache_key)
    
    if quiz is None:
        try:
            quiz = Quiz.objects.select_related('category').prefetch_related(
                'questions'
            ).get(id=quiz_id, is_active=True)
            cache.set(cache_key, quiz, timeout=600)  # 10 minutes
        except Quiz.DoesNotExist:
            return None
    
    return quiz


def invalidate_quiz_cache(quiz_id):
    """Invalidate cached quiz data"""
    cache_keys = [
        f'quiz_{quiz_id}',
        f'quiz_list_active',
        f'quiz_submissions_{quiz_id}'
    ]
    cache.delete_many(cache_keys)
    
    
    
def generate_quiz_statistics(quiz_id):
    """
    Generate statistics for a specific quiz.
    
    Args:
        quiz_id: Quiz ID
    
    Returns:
        dict: Quiz statistics
    """
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        submissions = Submission.objects.filter(quiz=quiz)
        
        if not submissions.exists():
            stats = {
                'quiz_id': quiz_id,
                'quiz_title': quiz.title,
                'total_attempts': 0,
                'message': 'No submissions found'
            }
            cache.set(f'quiz_stats_{quiz_id}', stats, timeout=3600)  # 1 hour cache
            return stats
        
        total_attempts = submissions.count()
        unique_users = submissions.values('user').distinct().count()
        average_score = submissions.aggregate(Avg('score'))['score__avg']
        highest_score = submissions.aggregate(Max('score'))['score__max']
        lowest_score = submissions.aggregate(Min('score'))['score__min']
        passed_count = submissions.filter(score__gte=quiz.passing_score).count()
        
        stats = {
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'total_attempts': total_attempts,
            'unique_users': unique_users,
            'average_score': round(average_score, 2) if average_score else 0,
            'highest_score': float(highest_score) if highest_score else 0,
            'lowest_score': float(lowest_score) if lowest_score else 0,
            'passed_count': passed_count,
            'failed_count': total_attempts - passed_count,
            'pass_rate': round((passed_count / total_attempts * 100), 2)
        }
        cache.set(f'quiz_stats_{quiz_id}', stats, timeout=3600)  # store in Redis
        return stats

        
    except Quiz.DoesNotExist:
        return {'error': 'Quiz not found'}
    except Exception as e:
        return {'error': str(e)}
