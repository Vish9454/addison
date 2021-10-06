from django.db.models import Q
from rest_framework.permissions import BasePermission
from core.messages import variables
from rest_framework.authtoken.models import Token
from accounts.models import User


class IsAdmin(BasePermission):
    message = variables.get("PERMISSION_MESSAGE")

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_role == User.ADMIN)


class IsUser(BasePermission):
    message = variables.get("PERMISSION_MESSAGE")

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_role == User.USER)
