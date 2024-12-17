from rest_framework import permissions

from ..utils import Constants

# Allow web browsers to query authenticated endpoints for OPTIONS without passing in authentication headers
class IsAuthenticated(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True

        if request.user.is_anonymous is False and request.user.status != Constants.USER_STATUS_ACTIVE:
            return False

        return super(IsAuthenticated, self).has_permission(request, view)


class IsAdminPermission(permissions.BasePermission):
    message = "Only admin accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == Constants.USER_ROLE_ADMIN


class IsSuperAdminPermission(permissions.BasePermission):
    message = "Only super admin accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == Constants.USER_ROLE_ADMIN and request.user.admin.role == Constants.ADMIN_ROLE_ADMIN


class IsCustomerPermission(permissions.BasePermission):
    message = "Only customer accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.status == Constants.USER_STATUS_ACTIVE and request.user.role == Constants.USER_ROLE_CUSTOMER


class IsDriverPermission(permissions.BasePermission):
    message = "Only driver accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == Constants.USER_ROLE_DRIVER


class IsCompanyMemberPermission(permissions.BasePermission):
    message = "Only company member accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == Constants.USER_ROLE_COMPANY_MEMBER


class IsCompanyMemberAdminPermission(permissions.BasePermission):
    message = "Only company member admin accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == Constants.USER_ROLE_COMPANY_MEMBER and request.user.admin.role == Constants.COMPANY_MEMBER_ROLE_ADMIN