# apps/jobs/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Job, Department
from .serializers import JobSerializer, DepartmentSerializer

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]