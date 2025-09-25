from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer_extended', 'Offer Extended'),
        ('offer_accepted', 'Offer Accepted'),
        ('offer_declined', 'Offer Declined'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    # Application Data
    resume = models.FileField(upload_to='applications/resumes/')
    cover_letter = models.TextField(blank=True)
    portfolio_links = models.JSONField(default=list)
    answers_to_questions = models.JSONField(default=dict)
    
    # ATS Scoring
    ats_score = models.FloatField(null=True, blank=True)
    skill_match_score = models.FloatField(null=True, blank=True)
    experience_match_score = models.FloatField(null=True, blank=True)
    education_match_score = models.FloatField(null=True, blank=True)
    keyword_match_score = models.FloatField(null=True, blank=True)
    ats_feedback = models.JSONField(default=dict)
    
    # Tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications_reviewed')
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        unique_together = ['job', 'candidate']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['ats_score']),
        ]

class ApplicationStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_status_history'
        ordering = ['-created_at']
