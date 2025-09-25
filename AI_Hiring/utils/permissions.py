from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['recruiter', 'admin']

class IsHiringManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['hiring_manager', 'recruiter', 'admin']

class IsInterviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['interviewer', 'hiring_manager', 'recruiter', 'admin']

class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'candidate'

class IsRecruiterOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['recruiter', 'admin']:
            return True
        if hasattr(obj, 'candidate'):
            return obj.candidate == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class RoleBasedPermission(permissions.BasePermission):
    """Dynamic role-based permission"""
    role_permissions = {
        'admin': ['all'],
        'recruiter': ['view_all', 'edit_jobs', 'manage_applications', 'schedule_interviews'],
        'hiring_manager': ['view_department', 'approve_offers', 'view_reports'],
        'interviewer': ['view_assigned', 'submit_feedback'],
        'candidate': ['apply_jobs', 'view_own_applications']
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        required_permission = getattr(view, 'required_permission', None)
        
        if not required_permission:
            return True
        
        if user_role == 'admin':
            return True
        
        user_permissions = self.role_permissions.get(user_role, [])
        return required_permission in user_permissions
