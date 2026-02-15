# ========================
# LIBRARIES
# ========================
from django.urls import path
from . import views

# ========================
# URLS
# ========================

urlpatterns = [

    # ============================ PUBLIC ============================ #
    path("", views.home, name="home"),
    path("redirect/", views.role_redirect, name="role_redirect"),
    path("profile-missing/", views.profile_missing, name="profile_missing"),

    # ============================ CEO ============================ #
    path("ceo/dashboard/", views.ceo_dashboard, name="ceo_dashboard"),
    path("ceo/departments/", views.ceo_departments, name="ceo_departments"),
    path("ceo/departments/add/", views.ceo_add_department, name="ceo_add_department"),
    path(
        "ceo/departments/<int:dept_id>/",
        views.ceo_department_detail,
        name="ceo_department_detail"
    ),
    path("ceo/users/", views.ceo_manage_users, name="ceo_users"),
    path("ceo/users/add/", views.ceo_add_profile, name="ceo_add_profile"),
    path("ceo/users/create/", views.ceo_create_user, name="ceo_create_user"),
    path(
        "ceo/users/<int:user_id>/details/",
        views.ceo_add_user_details,
        name="ceo_user_details"
    ),
    path(
        "ceo/feedback/",
        views.ceo_feedback_departments,
        name="ceo_feedback_departments"
    ),

    path(
        "ceo/feedback/<int:dept_id>/",
        views.ceo_department_feedback,
        name="ceo_department_feedback"
    ),

    # ============================ HOD ============================ #
    path("hod/dashboard/", views.hod_dashboard, name="hod_dashboard"),
    path("hod/users/", views.hod_manage_users, name="hod_manage_users"),
    path("hod/users/create/", views.hod_create_user, name="hod_create_user"),
    path(
        "hod/users/<int:user_id>/details/",
        views.hod_user_details,
        name="hod_user_details"
    ),
    path("hod/add-profile/", views.hod_add_profile, name="hod_add_profile"),
    path("hod/subjects/", views.hod_manage_subjects, name="hod_manage_subjects"),
    path("hod/subjects/add/", views.hod_add_subject, name="hod_add_subject"),
    path("hod/questions/", views.hod_manage_questions, name="hod_manage_questions"),
    path("hod/questions/add/", views.hod_add_question, name="hod_add_question"),
    path(
    "hod/questions/delete/<int:question_id>/",
    views.hod_delete_question,
    name="hod_delete_question"
    ),
    path("hod/feedback/", views.hod_feedback_overview, name="hod_feedback_overview"),
    path("hod/feedback/all/", views.hod_feedback_list, name="hod_feedback_list"),

    # ============================ TEACHER ============================ #    
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),

    # ================= SHARED (TEACHER + HOD) ================= #
    path(
        "feedback/subject/<int:subject_id>/",
        views.subject_feedback_detail,
        name="subject_feedback_detail"
    ),

    path(
        "teacher/subject/<int:subject_id>/comments/",
        views.subject_comments,
        name="subject_comments"
    ),

    # ============================ STUDENT ============================ #
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/feedback/", views.feedback_form, name="feedback_form"),
    path("student/history/", views.feedback_history, name="feedback_history"),
    path("student/progress/", views.student_progress, name="student_progress"),
    path("student/subjects/", views.student_subjects, name="student_subjects"),

]