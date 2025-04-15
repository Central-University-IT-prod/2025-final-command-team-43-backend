from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasOrganiserRole(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "organiser"


class IsOrganiserOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_org = request.user and request.user.role == "organiser"
        return is_org or request.method in SAFE_METHODS


class IsOrgOfThisContest(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "organiser"


class IsOrgOfFile(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.role == "organiser"
