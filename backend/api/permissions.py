from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user
                or request.method in permissions.SAFE_METHODS)

class IsAuthororAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.is_admin or obj.author == request.user
                or request.method in permissions.SAFE_METHODS)





class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_admin)



class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_admin or request.user.is_staff





class IsModer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.is_moderator
                or request.method in permissions.SAFE_METHODS)


class IsAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.is_admin
                or request.method in permissions.SAFE_METHODS)
