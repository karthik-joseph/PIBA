from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Permission to only allow owners of an object to access it."""

    def has_object_permission(self, request, view, obj):
        # Check if object has a 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsBuyer(permissions.BasePermission):
    """Permission for buyers only."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'buyer'
        )


class IsSeller(permissions.BasePermission):
    """Permission for sellers only."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'seller'
        )


class IsVerifiedSeller(permissions.BasePermission):
    """Permission for verified sellers only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role != 'seller':
            return False
        # Check if seller profile exists and is verified
        return (
            hasattr(request.user, 'seller_profile') and
            request.user.seller_profile.is_verified
        )


class IsAdmin(permissions.BasePermission):
    """Permission for admin users only."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_superuser)
        )


class IsBuyerOrSeller(permissions.BasePermission):
    """Permission for buyers or sellers."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['buyer', 'seller']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to allow owners or admins to access an object."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsSellerOwnerOrAdmin(permissions.BasePermission):
    """Permission for seller owners or admins."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        # Check if object has a seller attribute
        if hasattr(obj, 'seller'):
            return obj.seller.user == request.user
        return False


class ReadOnly(permissions.BasePermission):
    """Permission for read-only access."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow authenticated users full access, or read-only for unauthenticated.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
