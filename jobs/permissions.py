from rest_framework import permissions

class IsCompany(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'company'

class IsApplicant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'applicant'

class IsJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

class IsApplicationJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.job.created_by == request.user