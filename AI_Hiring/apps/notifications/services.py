from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    @shared_task
    def send_application_confirmation(application_id):
        """Send confirmation email when application is submitted"""
        from apps.applications.models import Application
        
        try:
            application = Application.objects.get(id=application_id)
            
            context = {
                'candidate_name': application.candidate.get_full_name(),
                'job_title': application.job.title,
                'company_name': 'Your Company',
                'application_id': application.id,
                'status_link': f"{settings.FRONTEND_URL}/applications/{application.id}"
            }
            
            html_content = render_to_string('emails/application_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=f'Application Received - {application.job.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.candidate.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Confirmation email sent for application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
            return False
    
    @staticmethod
    @shared_task
    def send_status_update(application_id, old_status, new_status):
        """Send email when application status changes"""
        from apps.applications.models import Application
        
        try:
            application = Application.objects.get(id=application_id)
            
            status_messages = {
                'shortlisted': 'Great news! Your application has been shortlisted.',
                'interview_scheduled': 'Your interview has been scheduled.',
                'rejected': 'Update on your application status.',
                'offer_extended': 'Congratulations! You have received an offer.',
            }
            
            context = {
                'candidate_name': application.candidate.get_full_name(),
                'job_title': application.job.title,
                'new_status': new_status,
                'message': status_messages.get(new_status, 'Your application status has been updated.'),
                'status_link': f"{settings.FRONTEND_URL}/applications/{application.id}"
            }
            
            html_content = render_to_string('emails/status_update.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=f'Application Update - {application.job.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.candidate.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Status update email sent for application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update email: {str(e)}")
            return False
    
    @staticmethod
    @shared_task
    def send_interview_invitation(interview_id):
        """Send interview invitation email"""
        from apps.interviews.models import Interview
        
        try:
            interview = Interview.objects.get(id=interview_id)
            
            context = {
                'candidate_name': interview.application.candidate.get_full_name(),
                'job_title': interview.application.job.title,
                'interview_type': interview.get_type_display(),
                'scheduled_at': interview.scheduled_at,
                'duration': interview.duration_minutes,
                'meeting_link': interview.meeting_link,
                'location': interview.location,
                'interviewers': [i.get_full_name() for i in interview.interviewers.all()]
            }
            
            html_content = render_to_string('emails/interview_invitation.html', context)
            text_content = strip_tags(html_content)
            
            # Send to candidate
            candidate_email = EmailMultiAlternatives(
                subject=f'Interview Invitation - {interview.application.job.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[interview.application.candidate.email]
            )
            candidate_email.attach_alternative(html_content, "text/html")
            candidate_email.send()
            
            # Send to interviewers
            for interviewer in interview.interviewers.all():
                interviewer_context = context.copy()
                interviewer_context['is_interviewer'] = True
                interviewer_context['interviewer_name'] = interviewer.get_full_name()
                
                html_content = render_to_string('emails/interview_invitation.html', interviewer_context)
                text_content = strip_tags(html_content)
                
                interviewer_email = EmailMultiAlternatives(
                    subject=f'Interview Scheduled - {interview.application.candidate.get_full_name()}',
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[interviewer.email]
                )
                interviewer_email.attach_alternative(html_content, "text/html")
                interviewer_email.send()
            
            logger.info(f"Interview invitation sent for interview {interview_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send interview invitation: {str(e)}")
            return False
    
    @staticmethod
    @shared_task
    def send_offer_letter(application_id, offer_details):
        """Send offer letter email"""
        from apps.applications.models import Application
        
        try:
            application = Application.objects.get(id=application_id)
            
            context = {
                'candidate_name': application.candidate.get_full_name(),
                'job_title': application.job.title,
                'offer_details': offer_details,
                'accept_link': f"{settings.FRONTEND_URL}/offers/{application.id}/accept",
                'decline_link': f"{settings.FRONTEND_URL}/offers/{application.id}/decline"
            }
            
            html_content = render_to_string('emails/offer_letter.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=f'Job Offer - {application.job.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.candidate.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Attach PDF offer letter if available
            if 'pdf_path' in offer_details:
                email.attach_file(offer_details['pdf_path'])
            
            email.send()
            
            logger.info(f"Offer letter sent for application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send offer letter: {str(e)}")
            return False
