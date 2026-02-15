from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models import Avg, Count
from .utils import get_user_profile, get_subject_improvement
from .models import (
    Department, Subject, Feedback, FeedbackResponse,
    FeedbackQuestion, Profile, StudentProfile, TeacherProfile
)
from django.contrib.auth.models import User

# =========================
# HELPER FUNCTIONS
# =========================

@login_required
def profile_missing(request):
    return render(request, "profile_missing.html")

def dashboard_url(user):
    role = user.profile.role
    return {
        "STUDENT": "student_dashboard",
        "TEACHER": "teacher_dashboard",
        "HOD": "hod_dashboard",
        "CEO": "ceo_dashboard",
    }.get(role, "home")

# =========================
# ROLE HELPERS
# =========================

def is_ceo(user):
    if user.is_superuser:
        return True

    return hasattr(user, "profile") and user.profile.role == "CEO"

def is_student(user):
    return hasattr(user, "profile") and user.profile.role == "STUDENT"

def is_teacher(user):
    return hasattr(user, "profile") and user.profile.role == "TEACHER"

# =========================
# HOME
# =========================

def home(request):
    return render(request, "home.html")

# =========================
# ROLE REDIRECT
# =========================

@login_required
def role_redirect(request):
    user = request.user

    if user.is_superuser:
        return redirect("ceo_dashboard")

    if not hasattr(user, "profile"):
        messages.error(
            request,
            "Your profile has not been created yet. Contact administrator."
        )
        return redirect("home")

    role = user.profile.role

    return redirect({
        "STUDENT": "student_dashboard",
        "TEACHER": "teacher_dashboard",
        "HOD": "hod_dashboard",
        "CEO": "ceo_dashboard",
    }.get(role, "home"))

# =========================
# CEO VIEWS
# =========================

@login_required
def ceo_dashboard(request):

    user = request.user

    if user.is_superuser:
        pass

    else:
        if not hasattr(user, "profile"):
            messages.error(
                request,
                "Your profile has not been created yet. Contact system administrator."
            )
            return redirect("home")

        if user.profile.role != "CEO":
            return HttpResponseForbidden()

    semester = request.GET.get("semester", settings.CURRENT_SEMESTER)
    month = request.GET.get("month", settings.CURRENT_MONTH)

    try:
        semester = int(semester)
        month = int(month)
    except (TypeError, ValueError):
        semester = settings.CURRENT_SEMESTER
        month = settings.CURRENT_MONTH

    departments = Department.objects.all()
    data = []

    total_feedbacks = 0
    rating_sum = 0
    rating_count = 0

    for dept in departments:
        subjects = Subject.objects.filter(
            teacher__profile__department=dept
        )

        feedbacks = Feedback.objects.filter(
            subject__in=subjects,
            semester=semester,
            month=month
        )

        feedback_count = feedbacks.count()
        total_feedbacks += feedback_count

        avg_rating = (
            FeedbackResponse.objects
            .filter(feedback__in=feedbacks)
            .aggregate(avg=Avg("rating"))["avg"]
        )

        if avg_rating:
            rating_sum += avg_rating * feedback_count
            rating_count += feedback_count

        avg = round(avg_rating or 0, 1) 

        data.append({
            "department": dept.name,
            "subjects": subjects.count(),
            "feedbacks": feedback_count,
            "average": avg,
            "percentage":  round((avg / 5) * 100, 1)
        })

    overall_avg = round(rating_sum / rating_count, 1) if rating_count else 0

    weakest_department = None

    rated_departments = [
        d for d in data if d["feedbacks"] > 0
    ]

    if rated_departments:
        weakest_department = min(
            rated_departments,
            key=lambda x: x["average"]
        )["department"]

    return render(request, "ceo/dashboard.html", {
        "data": data,
        "semester": semester,
        "month": month,
        "total_departments": departments.count(),
        "total_feedbacks": total_feedbacks,
        "overall_avg": overall_avg,
        "weakest_department": weakest_department,
    })

@login_required
def ceo_add_department(request):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        name = request.POST.get("name")

        if Department.objects.filter(name=name).exists():
            messages.error(request, "Department already exists.")
            return redirect("ceo_add_department")

        Department.objects.create(name=name)
        messages.success(request, "Department added successfully.")
        return redirect("ceo_departments")

    return render(request, "ceo/add_departments.html")

@login_required
def ceo_create_user(request):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("ceo_create_user")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("ceo_create_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("ceo_create_user")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            f"User '{username}' created successfully. Now create profile."
        )

        return redirect("ceo_add_profile")

    return render(request, "ceo/create_user.html")

@login_required
def ceo_add_profile(request):
    user = request.user

    if not user.is_superuser:
        if not hasattr(user, "profile") or user.profile.role != "CEO":
            return HttpResponseForbidden()

    users = User.objects.filter(profile__isnull=True)
    departments = Department.objects.all()

    preselected_user = request.GET.get("user")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        role = request.POST.get("role")
        department_id = request.POST.get("department_id")
        roll_no = request.POST.get("roll_no")

        if not user_id or not role:
            messages.error(request, "User and role are required.")
            return redirect("ceo_add_profile")

        target_user = get_object_or_404(User, id=user_id)

        if hasattr(target_user, "profile"):
            messages.error(request, "Profile already exists for this user.")
            return redirect("ceo_add_profile")

        if role != "CEO" and not department_id:
            messages.error(request, "Department is required for this role.")
            return redirect("ceo_add_profile")

        department = None
        if department_id:
            department = get_object_or_404(Department, id=department_id)

        profile = Profile.objects.create(
            user=target_user,
            role=role,
            department=department,
            created_by=request.user
        )

        if role == "TEACHER":
            TeacherProfile.objects.create(profile=profile)

        elif role == "STUDENT":
            if not roll_no:
                messages.error(request, "Roll number is required for students.")
                profile.delete()
                return redirect("ceo_add_profile")

            if StudentProfile.objects.filter(roll_no=roll_no).exists():
                messages.error(request, "Roll number already exists.")
                profile.delete()
                return redirect("ceo_add_profile")

            StudentProfile.objects.create(
                profile=profile,
                roll_no=roll_no
            )

        if role == "HOD":
            if not department:
                messages.error(request, "Department is required for HOD.")
                profile.delete()
                return redirect("ceo_add_profile")

            if department.hod:
                messages.error(
                    request,
                    f"{department.name} already has an HOD ({department.hod.username})."
                )
                profile.delete()
                return redirect("ceo_add_profile")

            department.hod = target_user
            department.save()

        messages.success(request, "Profile created successfully.")
        return redirect("ceo_users")

    return render(request, "ceo/add_profile.html", {
        "users": users,
        "departments": departments,
        "roles": Profile.ROLE_CHOICES,
        "preselected_user": preselected_user,
    })

@login_required
def ceo_add_user_details(request, user_id):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()

        messages.success(request, "User details updated successfully.")
        return redirect("ceo_users")

    return render(request, "ceo/user_details.html", {
        "target_user": user
    })

@login_required
def ceo_manage_users(request):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    profiles = Profile.objects.select_related("user", "department")
    departments = Department.objects.all()

    if request.method == "POST":
        profile_id = request.POST["profile"]
        role = request.POST["role"]
        department_id = request.POST.get("department")

        profile = get_object_or_404(Profile, id=profile_id)

        profile.role = role
        profile.department_id = department_id if department_id else None
        profile.save()

        if role == "HOD" and department_id:
            department = Department.objects.get(id=department_id)
            department.hod = profile.user
            department.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("ceo_users")

    return render(request, "ceo/users.html", {
        "profiles": profiles,
        "departments": departments
    })

@login_required
def ceo_departments(request):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    departments = Department.objects.all()

    return render(request, "ceo/departments.html", {
        "departments": departments
    })

@login_required
def ceo_department_detail(request, dept_id):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    department = get_object_or_404(Department, id=dept_id)
    semester = settings.CURRENT_SEMESTER
    month = settings.CURRENT_MONTH

    hod_user = department.hod
    hod = Profile.objects.filter(user=hod_user).first() if hod_user else None

    teachers = Profile.objects.filter(
        department=department,
        role__in=["TEACHER","HOD"]
    )

    teacher_data = []

    for profile in teachers:
        teacher_profile = getattr(profile, "teacherprofile", None)
        if not teacher_profile:
            continue

        subjects = Subject.objects.filter(teacher=teacher_profile)

        feedbacks = Feedback.objects.filter(
            subject__in=subjects,
            semester=semester,
            month=month
        )

        avg = (
            FeedbackResponse.objects
            .filter(feedback__in=feedbacks)
            .aggregate(avg=Avg("rating"))["avg"]
        )

        teacher_data.append({
            "teacher": profile.user,
            "subjects": subjects.count(),
            "feedbacks": feedbacks.count(),
            "average": round(avg or 0, 1)
        })

    return render(request, "ceo/departments_detail.html", {
        "department": department,
        "hod": hod,
        "teacher_data": teacher_data,
        "semester": semester,
        "month": month
    })

@login_required
def ceo_feedback_departments(request):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    departments = Department.objects.all()

    return render(request, "ceo/feedback_departments.html", {
        "departments": departments
    })

@login_required
def ceo_department_feedback(request, dept_id):
    if not is_ceo(request.user):
        return HttpResponseForbidden()

    department = get_object_or_404(Department, id=dept_id)

    teachers = TeacherProfile.objects.filter(
        profile__department=department
    )

    subjects = Subject.objects.filter(
        teacher__in=teachers
    )

    subject_data = []

    for subject in subjects:
        feedbacks = Feedback.objects.filter(subject=subject)

        avg = (
            FeedbackResponse.objects
            .filter(feedback__in=feedbacks)
            .aggregate(avg=Avg("rating"))["avg"] or 0
        )

        subject_data.append({
            "subject": subject,
            "teacher": subject.teacher.profile.user if subject.teacher else None,
            "feedback_count": feedbacks.count(),
            "average": round(avg, 2),
        })

    return render(request, "hod/feedback_overview.html", {
        "department": department,
        "subject_data": subject_data,
        "viewer_role": "CEO",  
    })

# =========================
# HOD VIEWS
# =========================

@login_required
def hod_dashboard(request):
    user = request.user

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        messages.error(
            request,
            "Your profile has not been created yet. Please contact the CEO."
        )
        return redirect("home")

    if profile.role != "HOD":
        return HttpResponseForbidden()

    department = profile.department
    if not department:
        messages.error(
            request,
            "No department assigned to your profile. Contact the CEO."
        )
        return redirect("home")

    semester = settings.CURRENT_SEMESTER
    month = settings.CURRENT_MONTH

    subjects = Subject.objects.filter(
        teacher__profile__department=department
    )

    subject_data = []
    total_feedbacks = 0
    rating_sum = 0
    rating_count = 0

    for subject in subjects:
        feedbacks = Feedback.objects.filter(
            subject=subject,
            semester=semester,
            month=month
        )

        feedback_count = feedbacks.count()
        total_feedbacks += feedback_count

        avg_rating = (
            FeedbackResponse.objects
            .filter(feedback__in=feedbacks)
            .aggregate(avg=Avg("rating"))["avg"]
        )

        if avg_rating:
            rating_sum += avg_rating
            rating_count += 1

        subject_data.append({
            "subject": subject,
            "teacher": subject.teacher.profile.user if subject.teacher else None,
            "feedback_count": feedback_count,
            "average": round(avg_rating or 0, 1),
        })

    total_subjects = subjects.count()

    overall_avg = (
        round(rating_sum / rating_count, 1)
        if rating_count > 0
        else "—"
    )

    return render(request, "hod/dashboard.html", {
        "department": department,
        "subject_data": subject_data,
        "total_subjects": total_subjects,
        "total_feedbacks": total_feedbacks,
        "overall_avg": overall_avg,
        "semester":semester,
        "month":month,
    })

@login_required
def hod_create_user(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    hod_department = request.user.profile.department

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role")

        # -------- VALIDATIONS --------
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("hod_create_user")

        if role not in ["STUDENT", "TEACHER"]:
            messages.error(request, "Invalid role selected.")
            return redirect("hod_create_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("hod_create_user")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        messages.success(
            request,
            f"User '{username}' created successfully. Now create profile."
        )

        return redirect("hod_add_profile")

    return render(request, "hod/create_user.html", {
        "department": hod_department
    })

@login_required
def hod_add_profile(request):
    user = request.user

    if not hasattr(user, "profile") or user.profile.role != "HOD":
        return HttpResponseForbidden()

    department = user.profile.department

    users = User.objects.filter(profile__isnull=True)

    if request.method == "POST":
        user_id = request.POST.get("user")
        role = request.POST.get("role")
        roll_no = request.POST.get("roll_no")

        if not user_id or not role:
            messages.error(request, "All fields are required.")
            return redirect("hod_add_profile")

        target_user = get_object_or_404(User, id=user_id)

        if hasattr(target_user, "profile"):
            messages.error(request, "Profile already exists.")
            return redirect("hod_add_profile")

        if role == "STUDENT":
            if not roll_no:
                messages.error(request, "Roll number is required for students.")
                return redirect("hod_add_profile")

            if StudentProfile.objects.filter(roll_no=roll_no).exists():
                messages.error(request, "Roll number already exists.")
                return redirect("hod_add_profile")

        profile = Profile.objects.create(
            user=target_user,
            role=role,
            department=department,
            created_by=request.user
        )

        if role == "STUDENT":
            StudentProfile.objects.create(
                profile=profile,
                roll_no=roll_no
            )

        elif role == "TEACHER":
            TeacherProfile.objects.create(profile=profile)

        messages.success(request, f"{role} profile created successfully.")
        return redirect("hod_dashboard")

    return render(request, "hod/add_profile.html", {
        "users": users,
        "department": department,
    })

@login_required
def hod_manage_users(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    department = request.user.profile.department

    profiles = Profile.objects.filter(
        department=department
    ).select_related("user")

    if request.method == "POST":
        profile_id = request.POST.get("profile")
        role = request.POST.get("role")

        profile = get_object_or_404(
            Profile,
            id=profile_id,
            department=department
        )

        if role in ["CEO", "HOD"]:
            messages.error(
                request,
                "You are not allowed to assign this role."
            )
            return redirect("hod_manage_users")

        profile.role = role
        profile.save()

        messages.success(request, "User updated successfully.")
        return redirect("hod_manage_users")

    return render(request, "hod/users.html", {
        "profiles": profiles,
        "departments": [department],  
    })

@login_required
def hod_user_details(request, user_id):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    hod_profile = request.user.profile
    hod_department = hod_profile.department

    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)

    if profile.department != hod_department:
        return HttpResponseForbidden("You cannot access users from other departments.")

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        user.save()

        if profile.role == "STUDENT":
            profile.roll_no = request.POST.get("roll_no", "").strip()
            profile.division = request.POST.get("division", "").strip()
            profile.save()

        messages.success(request, "User details updated successfully.")
        return redirect("hod_manage_users")

    return render(request, "hod/user_details.html", {
        "target_user": user,
        "profile": profile,
    })

@login_required
def hod_add_subject(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    department = request.user.profile.department
    teachers = TeacherProfile.objects.filter(
        profile__department=department
    )

    if request.method == "POST":
        name = request.POST.get("subject_name")
        semester = request.POST.get("semester")
        teacher_id = request.POST.get("teacher")

        teacher = None
        if teacher_id:
            teacher = get_object_or_404(
                TeacherProfile,
                id=teacher_id,
                profile__department=department
            )

        Subject.objects.create(
            subject_name=name,
            teacher=teacher,   
        )

        messages.success(request, "Subject added successfully.")
        return redirect("hod_manage_subjects")

    return render(request, "hod/add_subject.html", {
        "teachers": teachers
    })

@login_required
def hod_manage_subjects(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    department = request.user.profile.department

    subjects = Subject.objects.filter(
        teacher__profile__department=department
    ).select_related("teacher")

    return render(request, "hod/manage_subjects.html", {
        "subjects": subjects,
        "department": department
    })

@login_required
def hod_add_question(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    if request.method == "POST":
        text = request.POST.get("question_text", "").strip()

        if not text:
            messages.error(request, "Question text is required.")
            return redirect("hod_add_question")

        FeedbackQuestion.objects.create(question_text=text)

        messages.success(request, "Question added successfully.")
        return redirect("hod_manage_questions")

    return render(request, "hod/add_question.html")

@login_required
def hod_manage_questions(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    questions = FeedbackQuestion.objects.all().order_by("-id")

    return render(request, "hod/manage_questions.html", {
        "questions": questions
    })

@login_required
def hod_delete_question(request, question_id):
    if request.method != "POST":
        return HttpResponseForbidden()

    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    question = FeedbackQuestion.objects.filter(id=question_id).first()

    if not question:
        messages.warning(request, "Question already deleted.")
        return redirect("hod_manage_questions")

    question.delete()
    messages.success(request, "Question deleted successfully.")
    return redirect("hod_manage_questions")

@login_required
def hod_feedback_list(request):
    if request.user.profile.role != "HOD":
        return HttpResponseForbidden()

    hod_department = request.user.profile.department

    feedbacks = (
        FeedbackResponse.objects
        .select_related("feedback", "feedback__subject", "question")
        .filter(feedback__subject__teacher__profile__department=hod_department)
        .order_by("-feedback__submitted_on")
    )

    return render(request, "hod/feedback_list.html", {
        "feedbacks": feedbacks
    })

@login_required
def hod_feedback_overview(request):
    hod_profile = request.user.profile

    if hod_profile.role != "HOD":
        return redirect(dashboard_url(request.user))

    department = hod_profile.department

    teachers = TeacherProfile.objects.filter(
        profile__department=department
    )

    subjects = Subject.objects.filter(
        teacher__in=teachers
    ).select_related("teacher")

    subject_data = []

    for subject in subjects:
        feedbacks = Feedback.objects.filter(subject=subject)

        avg = (
            FeedbackResponse.objects
            .filter(feedback__in=feedbacks)
            .aggregate(avg=Avg("rating"))["avg"] or 0
        )

        subject_data.append({
            "subject": subject,
            "teacher": subject.teacher.profile.user,
            "feedback_count": feedbacks.count(),
            "average": round(avg, 2),
        })

    return render(request, "hod/feedback_overview.html", {
        "department": department,
        "subject_data": subject_data,
    })

# =========================
# TEACHER VIEWS
# =========================

@login_required
def teacher_dashboard(request):
    user = request.user

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        messages.error(
            request,
            "Your profile has not been created yet. Please contact your HOD."
        )
        return redirect("home")

    if profile.role != "TEACHER":
        messages.error(request, "Access denied.")
        return redirect("home")

    try:
        teacher = profile.teacherprofile
    except TeacherProfile.DoesNotExist:
        messages.error(
            request,
            "Teacher profile details are missing. Please contact your HOD."
        )
        return redirect("home")

    semester = settings.CURRENT_SEMESTER
    month = settings.CURRENT_MONTH

    subjects = Subject.objects.filter(teacher=teacher)

    feedbacks = Feedback.objects.filter(
        subject__in=subjects,
        semester=semester,
        month=month
    )

    total_subjects = subjects.count()
    total_feedbacks = feedbacks.count()

    overall_avg = (
        FeedbackResponse.objects
        .filter(feedback__in=feedbacks)
        .aggregate(avg=Avg("rating"))["avg"] or 0
    )

    dashboard_data = []

    for subject in subjects:
        subject_feedbacks = feedbacks.filter(subject=subject)

        responses = (
            FeedbackResponse.objects
            .filter(feedback__in=subject_feedbacks)
            .values("question__question_text")
            .annotate(average_rating=Avg("rating"))
        )

        comments = subject_feedbacks.exclude(
            comment__isnull=True
        ).exclude(comment__exact="")

        improvement = get_subject_improvement(
            subject=subject,
            semester=semester,
            month=month
        )

        dashboard_data.append({
            "subject": subject,
            "feedback_count": subject_feedbacks.count(),
            "responses": responses,
            "comments": comments,
            "improvement": improvement,
        })

    return render(request, "teacher/dashboard.html", {
        "dashboard_data": dashboard_data,
        "total_subjects": total_subjects,
        "total_feedbacks": total_feedbacks,
        "overall_avg": round(overall_avg, 1),
        "semester": semester,
        "month": month,
    })

@login_required
def subject_feedback_detail(request, subject_id):
    user = request.user

    if user.is_superuser:
        role = "CEO"
    else:
        if not hasattr(user, "profile"):
            return HttpResponseForbidden()

        role = user.profile.role

    if role not in ["TEACHER", "HOD", "CEO"]:
        return HttpResponseForbidden()

    if role == "TEACHER":
        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teacher=user.profile.teacherprofile
        )

    elif role == "HOD":
        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teacher__profile__department=user.profile.department
        )

    else:  
        subject = get_object_or_404(
            Subject,
            id=subject_id
        )

    semester = settings.CURRENT_SEMESTER

    selected_month = request.GET.get("month")
    try:
        selected_month = int(selected_month)
    except (TypeError, ValueError):
        selected_month = settings.CURRENT_MONTH

    if selected_month not in [1, 2, 3, 4]:
        selected_month = settings.CURRENT_MONTH

    monthly_feedbacks = Feedback.objects.filter(
        subject=subject,
        semester=semester,
        month=selected_month
    )

    responses = (
        FeedbackResponse.objects
        .filter(feedback__in=monthly_feedbacks)
        .values("question__question_text")
        .annotate(average_rating=Avg("rating"))
        .order_by("question__question_text")
    )

    weakest_topic = min(
        responses,
        key=lambda x: x["average_rating"],
        default=None
    )

    comments = (
        monthly_feedbacks
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .order_by("-id")
    )

    monthly_trend = (
        FeedbackResponse.objects
        .filter(
            feedback__subject=subject,
            feedback__semester=semester
        )
        .values("feedback__month")
        .annotate(avg_rating=Avg("rating"))
        .order_by("feedback__month")
    )

    improvement = None
    trend = list(monthly_trend)

    month_index = next(
        (i for i, m in enumerate(trend)
         if m["feedback__month"] == selected_month),
        None
    )

    if month_index is not None and month_index > 0:
        prev = trend[month_index - 1]["avg_rating"]
        curr = trend[month_index]["avg_rating"]

        if prev and prev > 0:
            percent = round(((curr - prev) / prev) * 100, 1)
        else:
            percent = 0

        if curr > prev:
            status = "improved"
        elif curr < prev:
            status = "declined"
        else:
            status = "stable"

        improvement = {
            "status": status,
            "percent": abs(percent)
        }

    return render(
        request,
        "teacher/subject_detail.html",
        {
            "subject": subject,
            "semester": semester,
            "selected_month": selected_month,
            "responses": responses,
            "comments": comments,
            "monthly_trend": monthly_trend,
            "weakest_topic": weakest_topic,
            "improvement": improvement,
            "available_months": [1, 2, 3, 4],
            "viewer_role": role,  
        }
    )

@login_required
def subject_comments(request, subject_id):
    user = request.user

    if user.is_superuser:
        role = "CEO"
    else:
        if not hasattr(user, "profile"):
            return HttpResponseForbidden()

        role = user.profile.role

    if role not in ["TEACHER", "HOD", "CEO"]:
        return HttpResponseForbidden()

    if role == "TEACHER":
        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teacher=user.profile.teacherprofile
        )

    elif role == "HOD":
        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teacher__profile__department=user.profile.department
        )

    else:  
        subject = get_object_or_404(
            Subject,
            id=subject_id
        )

    semester = settings.CURRENT_SEMESTER

    selected_month = request.GET.get("month")
    try:
        selected_month = int(selected_month)
    except (TypeError, ValueError):
        selected_month = settings.CURRENT_MONTH

    if selected_month not in [1, 2, 3, 4]:
        selected_month = settings.CURRENT_MONTH

    comments = (
        Feedback.objects
        .filter(
            subject=subject,
            semester=semester,
            month=selected_month
        )
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .order_by("-submitted_on")
    )

    return render(request, "teacher/subject_comments.html", {
        "subject": subject,
        "semester": semester,
        "selected_month": selected_month,
        "comments": comments,
        "available_months": [1, 2, 3, 4],
        "viewer_role": role,
    })

# ==========================
# STUDENT VIEWS
# ==========================

@login_required
def student_dashboard(request):
    user = request.user

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        messages.error(
            request,
            "Your profile has not been created yet. Please contact your HOD."
        )
        return redirect("home")

    if profile.role != "STUDENT":
        return redirect("home")

    try:
        student = profile.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(
            request,
            "Student profile details are missing. Please contact your HOD."
        )
        return redirect("home")

    semester = settings.CURRENT_SEMESTER
    month = settings.CURRENT_MONTH

    current_avg = (
        FeedbackResponse.objects
        .filter(
            feedback__student=student,
            feedback__semester=semester,
            feedback__month=month
        )
        .aggregate(avg=Avg("rating"))["avg"]
    )

    last_avg = None
    if month > 1:
        last_avg = (
            FeedbackResponse.objects
            .filter(
                feedback__student=student,
                feedback__semester=semester,
                feedback__month=month - 1
            )
            .aggregate(avg=Avg("rating"))["avg"]
        )

    progress = None
    status = "first"

    if current_avg is not None and last_avg is not None and last_avg > 0:
        raw_progress = ((current_avg - last_avg) / last_avg) * 100
        progress = round(abs(raw_progress), 1)

        if raw_progress > 1:
            status = "improved"
        elif raw_progress < -1:
            status = "declined"
        else:
            status = "stable"

    return render(request, "student/dashboard.html", {
        "current_semester": semester,
        "current_month": month,
        "progress": progress,
        "progress_status": status,
    })

@login_required
def student_subjects(request):
    profile = request.user.profile

    if profile.role != "STUDENT":
        return render(request, "403.html")

    student = profile.studentprofile
    department = student.profile.department

    subjects = Subject.objects.filter(
        teacher__profile__department=department
    )

    return render(request, "student/subjects.html", {
        "subjects": subjects
    })

@login_required
def student_progress(request):

    if not is_student(request.user):
        return redirect("home")

    student = request.user.profile.studentprofile
    semester = settings.CURRENT_SEMESTER

    department = student.profile.department

    subjects = Subject.objects.filter(
        teacher__profile__department=department
    )

    progress_data = []
    
    for subject in subjects:
        monthly_avg = (
            FeedbackResponse.objects
            .filter(
                feedback__subject = subject,
                feedback__semester = semester
            )
            .values("feedback__month")
            .annotate(avg=Avg("rating"))
            .order_by("feedback__month")
        )

        progress_data.append({
            "subject": subject,
            "monthly": monthly_avg
        })

    return render(request, "student/progress.html",{
        "progress_data": progress_data,
        "semester": semester
    })

@login_required
def feedback_form(request):
    if request.user.profile.role != "STUDENT":
        messages.error(request, "Access Denied! Students Only.")
        return redirect("home")

    student = request.user.profile.studentprofile
    semester = settings.CURRENT_SEMESTER
    month = settings.CURRENT_MONTH

    department = student.profile.department

    subjects = Subject.objects.filter(
        teacher__profile__department=department
    )

    questions = FeedbackQuestion.objects.filter()


    submitted_subjects = Feedback.objects.filter(
        student=student,
        semester=semester,
        month=month
    ).values_list("subject_id", flat=True)

    if request.method == "POST":
        subject_id = request.POST.get("subject")

        if not subject_id:
            messages.error(request, "Please select a subject.")
            return redirect("feedback_form")

        subject = get_object_or_404(Subject, id=subject_id)

        if Feedback.objects.filter(
            student=student,
            subject=subject,
            semester=semester,
            month=month
        ).exists():
            messages.error(request, "You already submitted feedback.")
            return redirect("student_dashboard")

        ratings = []
        for q in questions:
            r = request.POST.get(f"question_{q.id}")
            if r:
                ratings.append(int(r))

        comment = request.POST.get("comment", "").strip()

        if ratings and all(r == 1 for r in ratings) and not comment:
            messages.error(request, "Please explain why you rated all questions 1 star.")
            return redirect("feedback_form")

        feedback = Feedback.objects.create(
            student=student,
            subject=subject,
            semester=semester,
            month=month,
            comment=comment
        )

        for q in questions:
            rating = request.POST.get(f"question_{q.id}")
            if rating:
                FeedbackResponse.objects.create(
                    feedback=feedback,
                    question=q,
                    rating=rating
                )

        return redirect(f"{reverse('student_dashboard')}?submitted=1")

    return render(request, "student/feedback_form.html", {
        "subjects": subjects,
        "questions": questions,
        "submitted_subjects": submitted_subjects,
        "current_month": month,
        "current_semester": semester,
    })

@login_required
def feedback_history(request):
    if request.user.profile.role != "STUDENT":
        return redirect(dashboard_url(request.user))

    student = request.user.profile.studentprofile

    semester = request.GET.get("semester")
    month = request.GET.get("month")

    feedbacks = Feedback.objects.filter(student=student)

    if semester:
        feedbacks = feedbacks.filter(semester=semester)

    if month:
        feedbacks = feedbacks.filter(month=month)

    feedbacks = (
        feedbacks
        .select_related("subject")
        .prefetch_related("feedbackresponse_set__question")
        .order_by("subject__subject_name", "-semester", "-month")
    )

    semesters = (
        Feedback.objects
        .filter(student=student)
        .values_list("semester", flat=True)
        .distinct()
        .order_by("semester")
    )

    months = (
        Feedback.objects
        .filter(student=student)
        .values_list("month", flat=True)
        .distinct()
        .order_by("month")
    )

    return render(request, "student/history.html", {
        "feedbacks": feedbacks,
        "selected_semester": semester,
        "selected_month": month,
        "semesters": semesters,
        "months": months,
    })