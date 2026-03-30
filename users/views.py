from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.shortcuts import get_object_or_404

from .models import User, UserProfile, WishlistItem
from pets.models import Pet
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
    SellerRegistrationSerializer,
    WishlistItemSerializer,
)


# ============ API Views ============

class RegisterAPIView(generics.CreateAPIView):
    """API endpoint for user registration."""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Set Django session so template tags work
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class SellerRegisterAPIView(generics.CreateAPIView):
    """API endpoint for seller registration."""
    
    queryset = User.objects.all()
    serializer_class = SellerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Seller registration successful. Your account is pending verification.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """API endpoint for user login."""
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Set Django session so template tags ({% if user.is_authenticated %}) work
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutAPIView(APIView):
    """API endpoint for user logout."""
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        # Also clear Django session
        auth_logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    """API endpoint for user profile."""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        # Update user fields
        user_serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        # Update profile fields
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response({
            'message': 'Profile updated successfully',
            'profile': UserProfileSerializer(profile).data
        })


class PasswordChangeAPIView(APIView):
    """API endpoint for changing password."""
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Blacklist all existing tokens for this user
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        # Generate new tokens
        refresh = RefreshToken.for_user(request.user)

        return Response({
            'message': 'Password changed successfully',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class UserDetailAPIView(generics.RetrieveAPIView):
    """API endpoint to get current user details."""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class WishlistAPIView(generics.ListAPIView):
    """API endpoint to retrieve user's wishlist."""
    
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)


class WishlistToggleAPIView(APIView):
    """API endpoint to toggle a pet on the wishlist."""
    
    permission_classes = [IsAuthenticated]

    def post(self, request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        wishlist_item = WishlistItem.objects.filter(user=request.user, pet=pet).first()
        
        if wishlist_item:
            wishlist_item.delete()
            return Response({'status': 'removed', 'message': 'Removed from wishlist.'})
        else:
            WishlistItem.objects.create(user=request.user, pet=pet)
            return Response({'status': 'added', 'message': 'Added to wishlist.'}, status=201)


# ============ Template Views ============

class HomeView(View):
    """Homepage view."""
    
    def get(self, request):
        return render(request, 'pets/home.html')


class RegisterView(View):
    """Template view for user registration."""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'users/register.html')


class SellerRegisterView(View):
    """Template view for seller registration."""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'users/seller_register.html')


class LoginView(View):
    """Template view for user login."""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        next_url = request.GET.get('next', '/')
        return render(request, 'users/login.html', {'next': next_url})


class LogoutView(View):
    """Template view for user logout."""
    
    def get(self, request):
        auth_logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')

    def post(self, request):
        auth_logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')


class ProfileView(View):
    """Template view for user profile."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, 'users/profile.html', {'profile': profile})


class WishlistView(View):
    """Template view for user wishlist."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'users/wishlist.html')


# Helper function for views
def index(request):
    """Redirect index to home."""
    return redirect('home')


class TermsOfUseView(View):
    """Template view for Terms of Use."""
    def get(self, request):
        return render(request, 'legal/terms.html')


class RefundPolicyView(View):
    """Template view for Refund Policy."""
    def get(self, request):
        return render(request, 'legal/refund.html')


class PetCareTipsView(View):
    """Template view for Pet Care Tips."""
    def get(self, request):
        return render(request, 'pages/pet_care_tips.html')

class PetCareBlogView(View):
    """Template view for Pet Care Blog (authenticated only)."""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'pages/pet_care_blog.html')
