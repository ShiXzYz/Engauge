from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='documents/')
    title = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    # Optional link to a course (class)
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')

    def __str__(self):
        return self.title or str(self.id)


class GeneratedQuestion(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]
    KIND_CHOICES = [('mcq', 'Multiple Choice'), ('exit', 'Exit Ticket')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='generated_questions')
    text = models.TextField()
    choices = models.JSONField(default=list)  # list of strings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='mcq')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_kind_display()} from {self.document_id}: {self.text[:60]}"


class Poll(models.Model):
    FORMAT_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('speed_ranking', 'Speed Ranking'),
        ('team_battle', 'Team Battle'),
        ('meta_prediction', 'Meta Prediction'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    choices = models.JSONField(default=list)
    question_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='single_choice')
    correct_answer = models.IntegerField(null=True, blank=True)  # For team_battle: index of correct choice
    active = models.BooleanField(default=False)
    countdown_started = models.BooleanField(default=False)  # For speed_ranking: whether countdown has started
    countdown_start_time = models.DateTimeField(null=True, blank=True)  # For speed_ranking: when countdown started
    # Optional link to a course
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE, related_name='polls')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text[:80]


class PollResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    choice = models.JSONField()  # For single_choice: int, For speed_ranking: list of ints [rank1_idx, rank2_idx, ...]
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=['poll', 'choice'])]


class ExitTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt_text = models.TextField()
    active = models.BooleanField(default=False)
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.CASCADE, related_name='exit_tickets')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.prompt_text[:80]


class ExitTicketResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(ExitTicket, on_delete=models.CASCADE, related_name='responses')
    answer = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=['ticket'])]


class Profile(models.Model):
    ROLE_CHOICES = [('professor', 'Professor'), ('student', 'Student')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_created')
    join_code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    ROLE_CHOICES = [('student', 'Student'), ('professor', 'Professor')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'course')
