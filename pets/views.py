from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Count, Q

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

from .models import PetCategory, Breed, Pet, PetImage
from .serializers import (
    PetCategorySerializer,
    BreedSerializer,
    PetListSerializer,
    PetDetailSerializer,
    PetCreateSerializer,
    PetUpdateSerializer,
    PetImageUploadSerializer,
)
from .filters import PetFilter
from users.permissions import IsSeller, IsVerifiedSeller, IsSellerOwnerOrAdmin
from custom_admin.views import validate_image_upload


# ============ API Views ============

class CategoryListAPIView(generics.ListAPIView):
    """List all active pet categories."""
    
    serializer_class = PetCategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return PetCategory.objects.filter(is_active=True).annotate(
            pet_count=Count('pets', filter=Q(pets__status='available', pets__is_approved=True))
        ).order_by('display_order', 'name')


class BreedListAPIView(generics.ListAPIView):
    """List all active breeds."""
    
    serializer_class = BreedSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Breed.objects.filter(is_active=True).select_related('category')


class BreedByCategoryAPIView(generics.ListAPIView):
    """List breeds by category."""
    
    serializer_class = BreedSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Breed.objects.filter(
            category_id=category_id,
            is_active=True
        ).order_by('name')


class PetListAPIView(generics.ListAPIView):
    """List all available pets with filtering."""
    
    serializer_class = PetListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PetFilter
    
    def get_queryset(self):
        return Pet.objects.filter(
            status='available',
            is_approved=True,
            is_active=True
        ).select_related('category', 'breed', 'seller').order_by('-created_at')


class FeaturedPetsAPIView(generics.ListAPIView):
    """List featured pets for homepage."""
    
    serializer_class = PetListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Pet.objects.filter(
            status='available',
            is_approved=True,
            is_active=True,
            is_featured=True
        ).select_related('category', 'breed', 'seller').order_by('-created_at')[:12]


class PetDetailAPIView(generics.RetrieveAPIView):
    """Get pet details."""
    
    serializer_class = PetDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Pet.objects.filter(is_active=True).select_related(
            'category', 'breed', 'seller'
        ).prefetch_related('images', 'health_records')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SimilarPetsAPIView(generics.ListAPIView):
    """Get similar pets based on category and breed."""
    
    serializer_class = PetListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        pet = get_object_or_404(Pet, slug=slug)
        
        # Find similar pets (same category, preferably same breed)
        similar = Pet.objects.filter(
            category=pet.category,
            status='available',
            is_approved=True,
            is_active=True
        ).exclude(id=pet.id)
        
        # Prioritize same breed
        if pet.breed:
            similar = similar.order_by(
                models.Case(
                    models.When(breed=pet.breed, then=0),
                    default=1
                ),
                '-created_at'
            )
        else:
            similar = similar.order_by('-created_at')
        
        return similar[:8]


class MyPetListingsAPIView(generics.ListAPIView):
    """List seller's own pet listings."""
    
    serializer_class = PetListSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'seller_profile'):
            return Pet.objects.filter(
                seller=self.request.user.seller_profile,
                is_active=True
            ).order_by('-created_at')
        return Pet.objects.none()


class PetCreateAPIView(generics.CreateAPIView):
    """Create a new pet listing."""
    
    serializer_class = PetCreateSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user.seller_profile)


class PetUpdateAPIView(generics.UpdateAPIView):
    """Update a pet listing."""
    
    serializer_class = PetUpdateSerializer
    permission_classes = [IsAuthenticated, IsSellerOwnerOrAdmin]
    lookup_field = 'slug'
    
    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return Pet.objects.all()
        if hasattr(self.request.user, 'seller_profile'):
            return Pet.objects.filter(seller=self.request.user.seller_profile)
        return Pet.objects.none()


class PetImageUploadAPIView(APIView):
    """Upload images for a pet."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, slug):
        pet = get_object_or_404(Pet, slug=slug)
        
        # Check ownership
        if pet.seller.user != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to modify this pet.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'No images provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate all images before processing
        for image in images:
            is_valid, error_msg = validate_image_upload(image)
            if not is_valid:
                return Response(
                    {'error': f'Image "{image.name}" failed validation: {error_msg}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        created_images = []
        for i, image in enumerate(images):
            pet_image = PetImage.objects.create(
                pet=pet,
                image=image,
                is_primary=(i == 0 and not pet.images.exists()),
                display_order=pet.images.count() + i
            )
            created_images.append(PetImageUploadSerializer(pet_image).data)
        
        return Response({
            'message': f'{len(created_images)} image(s) uploaded successfully.',
            'images': created_images
        }, status=status.HTTP_201_CREATED)
    
    def delete(self, request, slug):
        pet = get_object_or_404(Pet, slug=slug)
        
        # Check ownership
        if pet.seller.user != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to modify this pet.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        image_id = request.data.get('image_id')
        if not image_id:
            return Response(
                {'error': 'image_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image = get_object_or_404(PetImage, id=image_id, pet=pet)
        image.delete()
        
        return Response({'message': 'Image deleted successfully.'})


class SellerStatesAPIView(APIView):
    """Return distinct states from seller profiles for filtering."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        from sellers.models import SellerProfile
        states = (
            SellerProfile.objects
            .filter(is_active=True, is_verified=True)
            .exclude(state='')
            .values_list('state', flat=True)
            .distinct()
            .order_by('state')
        )
        return Response(list(states))


# ============ Template Views ============

class PetListingView(View):
    """Template view for browsing all pets."""
    
    def get(self, request):
        categories = PetCategory.objects.filter(is_active=True).annotate(
            pet_count=Count('pets', filter=Q(pets__status='available', pets__is_approved=True))
        ).order_by('display_order', 'name')
        
        return render(request, 'pets/listing.html', {
            'categories': categories,
        })


class CategoryPetsView(View):
    """Redirect to listing page with category filter applied."""
    
    def get(self, request, slug):
        from django.http import HttpResponseRedirect
        # Redirect to the main listing page with the category filter
        return HttpResponseRedirect(f'/pets/?category={slug}')


class PetDetailView(View):
    """Template view for single pet details."""
    
    def get(self, request, slug):
        pet = get_object_or_404(
            Pet.objects.select_related('category', 'breed', 'seller')
            .prefetch_related('images', 'health_records'),
            slug=slug,
            is_active=True
        )
        
        # Increment view count
        pet.increment_views()
        
        # Get similar pets
        similar_pets = Pet.objects.filter(
            category=pet.category,
            status='available',
            is_approved=True,
            is_active=True
        ).exclude(id=pet.id).select_related('category', 'breed')[:4]
        
        # Check if logged-in user owns this pet already
        user_has_purchased = False
        user_has_adopted = False
        user_has_pending_adoption = False

        if request.user.is_authenticated:
            from orders.models import Order
            from adoption.models import AdoptionRequest

            user_has_purchased = Order.objects.filter(
                buyer=request.user,
                items__pet=pet,
                status__in=['confirmed', 'processing', 'shipped', 'delivered'],
                payment_status='paid'
            ).exists()

            if pet.listing_type == 'adoption':
                adoption_req = AdoptionRequest.objects.filter(
                    pet=pet,
                    applicant=request.user
                ).order_by('-submitted_at').first()

                if adoption_req:
                    if adoption_req.status in ['approved', 'completed']:
                        user_has_adopted = True
                    elif adoption_req.status not in ['rejected', 'withdrawn']:
                        user_has_pending_adoption = True

        return render(request, 'pets/detail.html', {
            'pet': pet,
            'similar_pets': similar_pets,
            'user_has_purchased': user_has_purchased,
            'user_has_adopted': user_has_adopted,
            'user_has_pending_adoption': user_has_pending_adoption,
        })


# Import models for Case/When
from django.db import models
