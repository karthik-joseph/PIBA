from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from .models import SellerProfile, SellerVerificationDocument
from .serializers import (
    SellerProfileSerializer,
    SellerProfileDetailSerializer,
    SellerProfileUpdateSerializer,
    SellerVerificationDocumentSerializer,
    SellerListSerializer,
    SellerDashboardStatsSerializer,
)
from users.permissions import IsSeller, IsAdmin, IsOwnerOrAdmin
from pets.models import Pet
from orders.models import Order


# ============ API Views ============

class SellerListAPIView(generics.ListAPIView):
    """List all verified sellers."""
    
    serializer_class = SellerListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return SellerProfile.objects.filter(
            is_verified=True,
            is_active=True
        ).order_by('-rating', '-total_sales')


class SellerDetailAPIView(generics.RetrieveAPIView):
    """Get public seller profile."""
    
    serializer_class = SellerProfileSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return SellerProfile.objects.filter(is_active=True)


class SellerProfileAPIView(APIView):
    """Get or update seller's own profile."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'Seller profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = SellerProfileDetailSerializer(request.user.seller_profile)
        return Response(serializer.data)
    
    def patch(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'Seller profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = SellerProfileUpdateSerializer(
            request.user.seller_profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Profile updated successfully.',
            'profile': SellerProfileDetailSerializer(request.user.seller_profile).data
        })


class SellerDashboardStatsAPIView(APIView):
    """Get seller dashboard statistics."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'Seller profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        seller = request.user.seller_profile
        pets = Pet.objects.filter(seller=seller)
        orders = Order.objects.filter(seller=seller)
        
        stats = {
            'total_pets': pets.count(),
            'available_pets': pets.filter(status='available', is_active=True).count(),
            'sold_pets': pets.filter(status='sold').count(),
            'pending_approval': pets.filter(is_approved=False, is_active=True).count(),
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status__in=['pending', 'confirmed']).count(),
            'completed_orders': orders.filter(status='delivered').count(),
            'total_revenue': orders.filter(
                status='delivered',
                payment_status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'total_reviews': seller.total_reviews,
            'average_rating': seller.rating,
        }
        
        serializer = SellerDashboardStatsSerializer(stats)
        return Response(serializer.data)


class SellerDocumentUploadAPIView(APIView):
    """Upload verification documents."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response({'error': 'Seller profile not found.'}, status=404)
        
        documents = SellerVerificationDocument.objects.filter(
            seller=request.user.seller_profile
        )
        serializer = SellerVerificationDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response({'error': 'Seller profile not found.'}, status=404)
        
        serializer = SellerVerificationDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user.seller_profile)
        
        return Response({
            'message': 'Document uploaded successfully.',
            'document': serializer.data
        }, status=status.HTTP_201_CREATED)


class SellerVerifyAPIView(APIView):
    """Verify or reject a seller (admin only)."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        seller = get_object_or_404(SellerProfile, pk=pk)
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if action == 'approve':
            seller.is_verified = True
            seller.verification_date = timezone.now()
            seller.save()
            return Response({'message': 'Seller verified successfully.'})
        elif action == 'reject':
            seller.is_verified = False
            seller.save()
            return Response({'message': 'Seller verification rejected.'})
        else:
            return Response(
                {'error': 'Invalid action. Use "approve" or "reject".'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============ Template Views ============

class SellerDashboardView(View):
    """Seller dashboard page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'seller':
            return redirect('home')
        return render(request, 'sellers/dashboard.html')


class SellerManagePetsView(View):
    """Seller pet management page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'seller':
            return redirect('home')
        return render(request, 'sellers/manage_pets.html')


class SellerAddPetView(View):
    """Add new pet form."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'seller':
            return redirect('home')
        return render(request, 'sellers/pet_form.html', {'mode': 'add'})


class SellerEditPetView(View):
    """Edit pet form."""
    
    def get(self, request, slug):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'seller':
            return redirect('home')
        
        pet = get_object_or_404(Pet, slug=slug, seller=request.user.seller_profile)
        return render(request, 'sellers/pet_form.html', {'mode': 'edit', 'pet': pet})


class SellerOrdersView(View):
    """Seller orders page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'seller':
            return redirect('home')
        return render(request, 'sellers/orders.html')


class SellerPublicProfileView(View):
    """Public seller profile page."""
    
    def get(self, request, pk):
        seller = get_object_or_404(SellerProfile, pk=pk, is_active=True)
        pets = Pet.objects.filter(
            seller=seller,
            status='available',
            is_approved=True,
            is_active=True
        )[:12]
        return render(request, 'sellers/public_profile.html', {
            'seller': seller,
            'pets': pets
        })
