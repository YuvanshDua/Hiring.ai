# apps/jobs/serializers.py
from rest_framework import serializers
from .models import Job, Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'department', 'department_name', 'description',
            'requirements', 'responsibilities', 'skills_required', 'skills_preferred',
            'job_type', 'experience_level', 'experience_min_years', 'experience_max_years',
            'salary_min', 'salary_max', 'location', 'is_remote', 'openings',
            'status', 'created_at', 'deadline', 'applications_count'
        ]
        read_only_fields = ['id', 'created_at', 'applications_count']
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_applications_count(self, obj):
        return obj.applications.count()
