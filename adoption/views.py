from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AdoptionRequest, AdoptionFollowUp
from .serializers import (
    AdoptionRequestCreateSerializer,
    AdoptionRequestListSerializer,
    AdoptionRequestDetailSerializer,
    AdoptionRequestUpdateSerializer,
    AdoptionFollowUpSerializer,
    AdoptionFollowUpCreateSerializer,
)
from pets.models import Pet
from users.permissions import IsSeller, IsAdmin


# ============ API Views ============

class AdoptionApplyAPIView(APIView):
    """Submit an adoption request."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AdoptionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pet_id = serializer.validated_data.pop('pet_id')
        pet = get_object_or_404(Pet, id=pet_id)
        
        # Validate pet is available for adoption
        if pet.listing_type != 'adoption':
            return Response(
                {'error': 'This pet is not available for adoption.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if pet.status != 'available':
            return Response(
                {'error': 'This pet is no longer available.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already applied
        if AdoptionRequest.objects.filter(pet=pet, applicant=request.user).exists():
            return Response(
                {'error': 'You have already submitted an adoption request for this pet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        adoption_request = AdoptionRequest.objects.create(
            pet=pet,
            applicant=request.user,
            **serializer.validated_data
        )
        
        return Response({
            'message': 'Adoption request submitted successfully.',
            'request': AdoptionRequestDetailSerializer(adoption_request).data
        }, status=status.HTTP_201_CREATED)


class MyAdoptionRequestsAPIView(generics.ListAPIView):
    """List user's own adoption requests."""
    
    serializer_class = AdoptionRequestListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AdoptionRequest.objects.filter(
            applicant=self.request.user
        ).order_by('-submitted_at')


class AdoptionRequestListAPIView(generics.ListAPIView):
    """List adoption requests for seller/admin."""
    
    serializer_class = AdoptionRequestListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all
        if user.is_superuser or user.role == 'admin':
            return AdoptionRequest.objects.all().order_by('-submitted_at')
        
        # Seller sees requests for their pets
        if hasattr(user, 'seller_profile'):
            return AdoptionRequest.objects.filter(
                pet__seller=user.seller_profile
            ).order_by('-submitted_at')
        
        return AdoptionRequest.objects.none()


class AdoptionRequestDetailAPIView(generics.RetrieveAPIView):
    """Get adoption request details."""
    
    serializer_class = AdoptionRequestDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'admin':
            return AdoptionRequest.objects.all()
        
        if hasattr(user, 'seller_profile'):
            return AdoptionRequest.objects.filter(
                pet__seller=user.seller_profile
            )
        
        return AdoptionRequest.objects.filter(applicant=user)


class AdoptionRequestUpdateAPIView(APIView):
    """Update adoption request status (seller/admin)."""
    
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        adoption_request = get_object_or_404(AdoptionRequest, pk=pk)
        
        # Check permission
        user = request.user
        if not (user.is_superuser or user.role == 'admin'):
            if not hasattr(user, 'seller_profile') or adoption_request.pet.seller != user.seller_profile:
                return Response({'error': 'Permission denied.'}, status=403)
        
        serializer = AdoptionRequestUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        new_status = data['status']
        
        # Update status
        adoption_request.status = new_status
        adoption_request.reviewed_at = timezone.now()
        
        if 'reviewer_notes' in data:
            adoption_request.reviewer_notes = data['reviewer_notes']
        
        if new_status == 'rejected' and 'rejection_reason' in data:
            adoption_request.rejection_reason = data['rejection_reason']
        
        if new_status == 'approved':
            # Update pet status
            adoption_request.pet.status = 'reserved'
            adoption_request.pet.save()
        
        if new_status == 'completed':
            adoption_request.completed_at = timezone.now()
            adoption_request.pet.status = 'adopted'
            adoption_request.pet.save()
        
        adoption_request.save()
        
        return Response({
            'message': 'Adoption request updated.',
            'request': AdoptionRequestDetailSerializer(adoption_request).data
        })


class AdoptionFollowUpAPIView(APIView):
    """Create or list follow-ups."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        adoption_request_id = request.query_params.get('request_id')
        if not adoption_request_id:
            return Response({'error': 'request_id is required.'}, status=400)
        
        follow_ups = AdoptionFollowUp.objects.filter(
            adoption_request_id=adoption_request_id
        )
        return Response(AdoptionFollowUpSerializer(follow_ups, many=True).data)
    
    def post(self, request):
        serializer = AdoptionFollowUpCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        adoption_request_id = serializer.validated_data.pop('adoption_request_id')
        adoption_request = get_object_or_404(AdoptionRequest, pk=adoption_request_id)
        
        # Check permission
        user = request.user
        if not (user.is_superuser or user.role == 'admin'):
            if not hasattr(user, 'seller_profile') or adoption_request.pet.seller != user.seller_profile:
                return Response({'error': 'Permission denied.'}, status=403)
        
        follow_up = AdoptionFollowUp.objects.create(
            adoption_request=adoption_request,
            conducted_by=request.user,
            **serializer.validated_data
        )
        
        return Response({
            'message': 'Follow-up scheduled.',
            'follow_up': AdoptionFollowUpSerializer(follow_up).data
        }, status=201)


# ============ Template Views ============

class AdoptionApplyView(View):
    """Adoption application form."""
    
    def get(self, request, pet_slug):
        if not request.user.is_authenticated:
            return redirect('login')
        pet = get_object_or_404(Pet, slug=pet_slug, listing_type='adoption', status='available')
        return render(request, 'adoption/apply.html', {'pet': pet})


class MyAdoptionRequestsView(View):
    """User's adoption requests page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'adoption/my_requests.html')


class AdoptionRequestDetailView(View):
    """Adoption request detail page."""
    
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')
        
        adoption_request = get_object_or_404(AdoptionRequest, pk=pk)
        
        # Check permission
        user = request.user
        has_access = (
            user.is_superuser or
            user.role == 'admin' or
            adoption_request.applicant == user or
            (hasattr(user, 'seller_profile') and adoption_request.pet.seller == user.seller_profile)
        )
        
        if not has_access:
            return redirect('home')
        
        return render(request, 'adoption/request_detail.html', {'adoption_request': adoption_request})
