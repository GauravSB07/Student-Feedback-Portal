from .models import Profile

def dashboard_url(request):
    user = request.user

    if not user.is_authenticated:
        return {"dashboard_url": None}

    if user.is_superuser:
        return {"dashboard_url": "ceo_dashboard"}

    if not hasattr(user, "profile"):
        return {"dashboard_url": None}

    role = user.profile.role

    return {
        "dashboard_url": {
            "STUDENT": "student_dashboard",
            "TEACHER": "teacher_dashboard",
            "HOD": "hod_dashboard",
            "CEO": "ceo_dashboard",
        }.get(role)
    }


def current_page(request):
    return {
        "current_path": request.path
    }
