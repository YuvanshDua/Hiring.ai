# This should replace your existing apps/jobs/models.py

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'departments'

class Job(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('executive', 'Executive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    requirements = models.JSONField(default=list)
    responsibilities = models.JSONField(default=list)
    skills_required = models.JSONField(default=list)
    skills_preferred = models.JSONField(default=list)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    experience_min_years = models.IntegerField(default=0)
    experience_max_years = models.IntegerField(null=True, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    is_remote = models.BooleanField(default=False)
    openings = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_created')
    hiring_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_managed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    # ATS Configuration
    auto_reject_threshold = models.IntegerField(default=40)
    auto_shortlist_threshold = models.IntegerField(default=70)
    screening_questions = models.JSONField(default=list)
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'jobs'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['department', 'status']),
        ]