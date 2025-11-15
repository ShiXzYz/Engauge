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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    choices = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text[:80]


class PollResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    choice = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=['poll', 'choice'])]


class ExitTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt_text = models.TextField()
    active = models.BooleanField(default=True)
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
