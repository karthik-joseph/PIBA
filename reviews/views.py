from django.shortcuts import render, get_object_or_404, redirect
from django.views import View

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import PetReview, SellerReview, ReviewResponse
from .serializers import (
    PetReviewSerializer,
    PetReviewCreateSerializer,
    SellerReviewSerializer,
    SellerReviewCreateSerializer,
    ReviewResponseCreateSerializer,
)
from pets.models import Pet
from sellers.models import SellerProfile
from orders.models import Order
from users.permissions import IsSeller, IsAdmin


# ============ Pet Review API Views ============

class PetReviewListAPIView(generics.ListAPIView):
    """List reviews for a pet."""
    
    serializer_class = PetReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        pet_slug = self.kwargs.get('pet_slug')
        return PetReview.objects.filter(
            pet__slug=pet_slug,
            is_approved=True
        ).select_related('reviewer').order_by('-created_at')


class PetReviewCreateAPIView(APIView):
    """Create a review for a pet."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pet_slug):
        pet = get_object_or_404(Pet, slug=pet_slug)
        
        # Check if user has already reviewed this pet
        if PetReview.objects.filter(pet=pet, reviewer=request.user).exists():
            return Response(
                {'error': 'You have already reviewed this pet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has purchased this pet
        order = Order.objects.filter(
            buyer=request.user,
            items__pet=pet,
            status='delivered'
        ).first()
        
        serializer = PetReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = PetReview.objects.create(
            pet=pet,
            reviewer=request.user,
            order=order,
            is_verified_purchase=order is not None,
            **serializer.validated_data
        )
        
        return Response({
            'message': 'Review submitted successfully.',
            'review': PetReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)


# ============ Seller Review API Views ============

class SellerReviewListAPIView(generics.ListAPIView):
    """List reviews for a seller."""
    
    serializer_class = SellerReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        seller_id = self.kwargs.get('seller_id')
        return SellerReview.objects.filter(
            seller_id=seller_id,
            is_approved=True
        ).select_related('reviewer').order_by('-created_at')


class SellerReviewCreateAPIView(APIView):
    """Create a review for a seller."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, seller_id):
        seller = get_object_or_404(SellerProfile, id=seller_id)
        
        # Check if user has already reviewed this seller
        if SellerReview.objects.filter(seller=seller, reviewer=request.user).exists():
            return Response(
                {'error': 'You have already reviewed this seller.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has purchased from this seller
        order = Order.objects.filter(
            buyer=request.user,
            seller=seller,
            status='delivered'
        ).first()
        
        serializer = SellerReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = SellerReview.objects.create(
            seller=seller,
            reviewer=request.user,
            order=order,
            is_verified_purchase=order is not None,
            **serializer.validated_data
        )
        
        return Response({
            'message': 'Review submitted successfully.',
            'review': SellerReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)


# ============ Review Response & Moderation ============

class ReviewResponseAPIView(APIView):
    """Respond to a review (seller only)."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    
    def post(self, request, pk):
        serializer = ReviewResponseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        if data['review_type'] == 'pet':
            review = get_object_or_404(PetReview, pk=pk)
            if review.pet.seller.user != request.user:
                return Response({'error': 'Permission denied.'}, status=403)
            
            response, created = ReviewResponse.objects.update_or_create(
                review_type='pet',
                pet_review=review,
                defaults={
                    'responder': request.user,
                    'response_text': data['response_text']
                }
            )
        else:
            review = get_object_or_404(SellerReview, pk=pk)
            if review.seller.user != request.user:
                return Response({'error': 'Permission denied.'}, status=403)
            
            response, created = ReviewResponse.objects.update_or_create(
                review_type='seller',
                seller_review=review,
                defaults={
                    'responder': request.user,
                    'response_text': data['response_text']
                }
            )
        
        return Response({
            'message': 'Response submitted successfully.' if created else 'Response updated.'
        })


class ReviewModerateAPIView(APIView):
    """Moderate a review (admin only)."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        review_type = request.data.get('review_type', 'pet')
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if review_type == 'pet':
            review = get_object_or_404(PetReview, pk=pk)
        else:
            review = get_object_or_404(SellerReview, pk=pk)
        
        if action == 'approve':
            review.is_approved = True
        elif action == 'reject':
            review.is_approved = False
        else:
            return Response({'error': 'Invalid action.'}, status=400)
        
        review.save()
        return Response({'message': f'Review {action}d successfully.'})


# ============ Template Views ============

class WriteReviewView(View):
    """Write review page."""
    
    def get(self, request, pet_slug):
        if not request.user.is_authenticated:
            return redirect('login')
        pet = get_object_or_404(Pet, slug=pet_slug)
        return render(request, 'reviews/write_review.html', {'pet': pet})
