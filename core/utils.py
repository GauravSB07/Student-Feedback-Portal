from django.db.models import Avg
from .models import Feedback, FeedbackResponse,Profile

def get_subject_improvement(subject, semester, month):

    if month <= 1:
        return "first"

    # Current month average #
    current_avg = (
        FeedbackResponse.objects
        .filter(
            feedback__subject=subject,
            feedback__semester=semester,
            feedback__month=month
        )
        .aggregate(avg=Avg("rating"))["avg"]
    )

    # Previous month average #
    prev_avg = (
        FeedbackResponse.objects
        .filter(
            feedback__subject=subject,
            feedback__semester=semester,
            feedback__month=month - 1
        )
        .aggregate(avg=Avg("rating"))["avg"]
    )

    # If no previous data #
    if prev_avg is None:
        return "first"

    # Safety #
    if current_avg is None:
        return "stable"

    # Compare #
    if current_avg > prev_avg:
        return "improved"
    elif current_avg < prev_avg:
        return "declined"
    else:
        return "stable"

def get_user_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None
