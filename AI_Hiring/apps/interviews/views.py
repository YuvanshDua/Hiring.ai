# apps/interviews/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Interview
from .serializers import InterviewSerializer

class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]