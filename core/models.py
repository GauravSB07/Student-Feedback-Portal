from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# -----------------------------
# DEPARTMENT
# -----------------------------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    hod = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hod_of_department"
    )

    def __str__(self):
        return self.name

# -----------------------------
# PROFILE (ROLE HOLDER)
# -----------------------------
class Profile(models.Model):
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('HOD', 'HOD'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    ]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_profiles"
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

# -----------------------------
# STUDENT PROFILE
# -----------------------------
class StudentProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.profile.user.username

# -----------------------------
# TEACHER PROFILE
# -----------------------------
class TeacherProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return self.profile.user.username

# -----------------------------
# SUBJECT
# -----------------------------
class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    def __str__(self):
        return self.subject_name

# -----------------------------
# FEEDBACK
# -----------------------------
class Feedback(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    semester = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()

    submitted_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'subject', 'semester', 'month')

    def __str__(self):
        return f"{self.subject} | Sem {self.semester} | Month {self.month}"

# -----------------------------
# FEEDBACK QUESTIONS
# -----------------------------
class FeedbackQuestion(models.Model):
    question_text = models.CharField(max_length=300)

    def __str__(self):
        return self.question_text

# -----------------------------
# FEEDBACK RESPONSES
# -----------------------------
class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.feedback} - {self.question}"
