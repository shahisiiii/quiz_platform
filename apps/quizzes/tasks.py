"""
Celery tasks for asynchronous operations.
Includes user report generation and email notifications.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Submission
import logging

logger = logging.getLogger(__name__)



@shared_task(name='send_submission_notification')
def send_submission_notification(submission_id):
    """
    Send email notification after quiz submission.
    This is a placeholder - requires email configuration in settings.
    
    Args:
        submission_id: Submission ID
    """
    try:
        submission = Submission.objects.select_related('user', 'quiz').get(
            id=submission_id
        )
        
        subject = f"Quiz Submission: {submission.quiz.title}"
        message = f"""
        Dear {submission.user.username},
        
        You have successfully submitted the quiz: {submission.quiz.title}
        
        Your Results:
        - Score: {submission.score}%
        - Marks: {submission.obtained_marks}/{submission.total_marks}
        - Status: {'Passed' if submission.score >= submission.quiz.passing_score else 'Failed'}
        
        Thank you for taking the quiz!
        """
        
        # Uncomment when email is configured
        # send_mail(
        #     subject,
        #     message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [submission.user.email],
        #     fail_silently=True,
        # )
        
        logger.info(f"Notification sent for submission {submission_id}")
        return {'status': 'success', 'submission_id': submission_id}
        
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return {'error': 'Submission not found'}
    except Exception as e:
        logger.error(f"Error sending notification for submission {submission_id}: {str(e)}")
        return {'error': str(e)}


@shared_task(name='cleanup_old_cache')
def cleanup_old_cache():
    """
    Periodic task to clean up old cached data.
    Can be scheduled with Celery Beat.
    """
    from django.core.cache import cache
    
    try:
        # This is a placeholder - implement specific cache cleanup logic
        logger.info("Cache cleanup task executed")
        return {'status': 'success', 'message': 'Cache cleanup completed'}
    except Exception as e:
        logger.error(f"Error in cache cleanup: {str(e)}")
        return {'error': str(e)}