from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from .models import Application, ApplicationStatusHistory
from .serializers import ApplicationSerializer, ApplicationDetailSerializer
from apps.ats.services import ATSService, ApplicationFilterService
from apps.notifications.services import EmailService
from utils.permissions import IsRecruiterOrOwner, IsRecruiter

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'job', 'candidate']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'candidate__email']
    ordering_fields = ['created_at', 'ats_score', 'submitted_at']
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsRecruiterOrOwner()]
        else:
            return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ApplicationDetailSerializer
        return ApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'candidate':
            return queryset.filter(candidate=user)
        elif user.role in ['recruiter', 'hiring_manager']:
            return queryset
        else:
            return queryset.none()
    
    @transaction.atomic
    def create(self, request):
        """Create new application with ATS scoring"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set candidate
        serializer.validated_data['candidate'] = request.user
        
        # Save application
        application = serializer.save()
        
        # Calculate ATS score
        ats_service = ATSService()
        ats_result = ats_service.calculate_ats_score(application, application.job)
        
        # Update application with scores
        application.ats_score = ats_result['total_score']
        application.skill_match_score = ats_result['scores']['skill_match']
        application.experience_match_score = ats_result['scores']['experience_match']
        application.education_match_score = ats_result['scores']['education_match']
        application.keyword_match_score = ats_result['scores']['keyword_match']
        application.ats_feedback = ats_result['feedback']
        
        # Auto-process based on thresholds
        if application.ats_score < application.job.auto_reject_threshold:
            application.status = 'rejected'
            application.rejection_reason = 'ATS score below threshold'
        elif application.ats_score >= application.job.auto_shortlist_threshold:
            application.status = 'shortlisted'
        else:
            application.status = 'under_review'
        
        application.submitted_at = timezone.now()
        application.save()
        
        # Send confirmation email
        EmailService.send_application_confirmation.delay(application.id)
        
        return Response(
            ApplicationDetailSerializer(application).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def update_status(self, request, pk=None):
        """Update application status with history tracking"""
        application = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = application.status
        
        # Create status history
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            reason=reason
        )
        
        # Update application
        application.status = new_status
        if new_status == 'rejected':
            application.rejection_reason = reason
        application.save()
        
        # Send status update email
        EmailService.send_status_update.delay(application.id, old_status, new_status)
        
        return Response({'status': 'updated'})
    
    @action(detail=False, methods=['post'], permission_classes=[IsRecruiter])
    def bulk_filter(self, request):
        """Bulk filter applications with advanced criteria"""
        filter_service = ApplicationFilterService()
        
        queryset = self.get_queryset()
        filters = request.data.get('filters', {})
        ranking = request.data.get('ranking', 'ats_score')
        
        # Apply filters
        filtered_qs = filter_service.filter_applications(queryset, filters)
        
        # Rank applications
        applications = list(filtered_qs)
        ranked_applications = filter_service.rank_applications(applications, ranking)
        
        serializer = ApplicationSerializer(ranked_applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ats_report(self, request, pk=None):
        """Get detailed ATS report for an application"""
        application = self.get_object()
        
        return Response({
            'ats_score': application.ats_score,
            'skill_match_score': application.skill_match_score,
            'experience_match_score': application.experience_match_score,
            'education_match_score': application.education_match_score,
            'keyword_match_score': application.keyword_match_score,
            'feedback': application.ats_feedback,
        })
