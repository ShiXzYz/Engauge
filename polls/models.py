from django.db import models
from django.utils import timezone
import uuid


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='documents/')
    title = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title or str(self.id)


class GeneratedQuestion(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='generated_questions')
    text = models.TextField()
    choices = models.JSONField(default=list)  # list of strings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Q from {self.document_id}: {self.text[:60]}"


class Poll(models.Model):
    FORMAT_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('speed_ranking', 'Speed Ranking'),
        ('team_battle', 'Team Battle'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    choices = models.JSONField(default=list)
    question_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='single_choice')
    correct_answer = models.IntegerField(null=True, blank=True)  # For team_battle: index of correct choice
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text[:80]


class PollResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    choice = models.JSONField()  # For single_choice: int, For speed_ranking: list of ints [rank1_idx, rank2_idx, ...]
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=['poll'])]
