# apps/applications/serializers.py
from rest_framework import serializers
from .models import Application, ApplicationStatusHistory
from apps.jobs.models import Job
from apps.users.models import User

class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'candidate', 'status', 'resume', 'cover_letter',
            'portfolio_links', 'answers_to_questions', 'ats_score',
            'submitted_at', 'candidate_name', 'job_title'
        ]
        read_only_fields = ['id', 'candidate', 'ats_score', 'submitted_at']
    
    def get_candidate_name(self, obj):
        return f"{obj.candidate.first_name} {obj.candidate.last_name}"
    
    def get_job_title(self, obj):
        return obj.job.title

class ApplicationDetailSerializer(ApplicationSerializer):
    status_history = serializers.SerializerMethodField()
    
    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + [
            'skill_match_score', 'experience_match_score', 'education_match_score',
            'keyword_match_score', 'ats_feedback', 'notes', 'status_history'
        ]
    
    def get_status_history(self, obj):
        return obj.status_history.values('from_status', 'to_status', 'created_at', 'reason')
