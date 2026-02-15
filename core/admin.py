# ========================
# LIBRARIES
# ========================
from django.contrib import admin
from django.contrib.auth.models import User
from .models import (
    Department, Profile,
    StudentProfile, TeacherProfile,
    Subject, Feedback,
    FeedbackQuestion, FeedbackResponse
)

admin.site.has_permission = lambda request: request.user.is_superuser

# ========================
# DEPARTMENT MODEL
# ========================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


# ========================
# PROFILE MODEL
# ========================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "created_by")
    list_filter = ("role", "department")
    search_fields = ("user__username", "user__email")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if request.resolver_match.kwargs.get("object_id"):
                # Editing existing profile → keep current user
                kwargs["queryset"] = User.objects.all()
            else:
                # Creating new profile → only users WITHOUT profile
                kwargs["queryset"] = User.objects.filter(profile__isnull=True)

        if db_field.name == "created_by":
            kwargs["queryset"] = User.objects.filter(
                profile__role__in=["CEO", "HOD"]
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("user", "created_by")
        return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile") and request.user.profile.role == "HOD":
            return qs.filter(department=request.user.profile.department)

        return qs.none()

    def save_model(self, request, obj, form, change):
        # Auto-assign department for HOD
        if (
            hasattr(request.user, "profile")
            and request.user.profile.role == "HOD"
        ):
            obj.department = request.user.profile.department

        # Auto-assign creator if not set
        if not obj.created_by:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

# ========================
# STUDENT PROFILE MODEL
# ========================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("profile", "roll_no")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile") and request.user.profile.role == "HOD":
            return qs.filter(profile__department=request.user.profile.department)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profile":
            qs = Profile.objects.filter(
                role="STUDENT",
                studentprofile__isnull=True
            )

            
            if (
                hasattr(request.user, "profile")
                and request.user.profile.role == "HOD"
            ):
                qs = qs.filter(
                    department=request.user.profile.department
                )

            kwargs["queryset"] = qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ========================
# TEACHER PROFILE MODEL
# ========================
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("profile",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile") and request.user.profile.role == "HOD":
            return qs.filter(profile__department=request.user.profile.department)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profile":
            kwargs["queryset"] = Profile.objects.filter(
                role="TEACHER",
                teacherprofile__isnull=True
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ========================
# SUBJECT MODEL
# ========================
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_name", "teacher", "created_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile") and request.user.profile.role == "HOD":
            return qs.filter(
                teacher__profile__department=request.user.profile.department
            )

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            if hasattr(request.user, "profile") and request.user.profile.role == "HOD":
                kwargs["queryset"] = TeacherProfile.objects.filter(
                    profile__department=request.user.profile.department
                )

        if db_field.name == "created_by":
            kwargs["queryset"] = User.objects.filter(
                profile__role__in=["CEO", "HOD"]
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# ========================
# FEEDBACK MODEL
# ========================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "semester", "month", "submitted_on")
    list_filter = ("semester", "month", "subject")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile"):
            role = request.user.profile.role

            if role == "HOD":
                return qs.filter(
                    subject__teacher__profile__department=request.user.profile.department
                )

            if role == "TEACHER":
                return qs.filter(
                    subject__teacher__profile=request.user.profile
                )

        return qs.none()


@admin.register(FeedbackQuestion)
class FeedbackQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text",)


@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ("feedback", "question", "rating")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "profile"):
            role = request.user.profile.role

            if role == "HOD":
                return qs.filter(
                    feedback__subject__teacher__profile__department=request.user.profile.department
                )

            if role == "TEACHER":
                return qs.filter(
                    feedback__subject__teacher__profile=request.user.profile
                )

        return qs.none()


