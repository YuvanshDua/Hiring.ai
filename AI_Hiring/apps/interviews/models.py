from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Interview(models.Model):
    TYPE_CHOICES = [
        ('phone_screening', 'Phone Screening'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('system_design', 'System Design'),
        ('cultural_fit', 'Cultural Fit'),
        ('final', 'Final Interview'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE, related_name='interviews')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Schedule
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Participants
    interviewers = models.ManyToManyField(User, related_name='interviews_conducted')
    
    # Feedback
    feedback = models.JSONField(default=dict)
    rating = models.IntegerField(null=True, blank=True)
    recommendation = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'interviews'
        ordering = ['scheduled_at']

class InterviewFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='feedback_entries')
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Ratings
    technical_skills = models.IntegerField(null=True, blank=True)
    communication = models.IntegerField(null=True, blank=True)
    problem_solving = models.IntegerField(null=True, blank=True)
    cultural_fit = models.IntegerField(null=True, blank=True)
    overall_rating = models.IntegerField()
    
    # Feedback
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    recommendation = models.CharField(max_length=20, choices=[
        ('strong_yes', 'Strong Yes'),
        ('yes', 'Yes'),
        ('maybe', 'Maybe'),
        ('no', 'No'),
        ('strong_no', 'Strong No'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interview_feedback'
        unique_together = ['interview', 'interviewer']

