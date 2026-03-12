from rest_framework import serializers
from .models import SellerProfile, SellerVerificationDocument
from users.serializers import UserSerializer


class SellerProfileSerializer(serializers.ModelSerializer):
    """Serializer for public seller profile."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user_email', 'business_name', 'business_type',
            'description', 'logo', 'website', 'phone',
            'city', 'state', 'country',
            'is_verified', 'rating', 'total_reviews', 'total_sales',
            'active_pet_count', 'full_address', 'joined_at'
        ]
        read_only_fields = [
            'id', 'is_verified', 'rating', 'total_reviews',
            'total_sales', 'joined_at'
        ]


class SellerProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for seller's own profile."""
    
    user = UserSerializer(read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'business_name', 'business_type',
            'registration_number', 'description', 'logo', 'website',
            'phone', 'address', 'city', 'state', 'country', 'postal_code',
            'is_verified', 'is_active', 'verification_date',
            'rating', 'total_reviews', 'total_sales', 'total_pets_listed',
            'full_address', 'joined_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_verified', 'verification_date',
            'rating', 'total_reviews', 'total_sales', 'total_pets_listed',
            'joined_at', 'updated_at'
        ]


class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating seller profile."""
    
    class Meta:
        model = SellerProfile
        fields = [
            'business_name', 'business_type', 'registration_number',
            'description', 'logo', 'website', 'phone',
            'address', 'city', 'state', 'country', 'postal_code'
        ]


class SellerVerificationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for seller verification documents."""
    
    class Meta:
        model = SellerVerificationDocument
        fields = [
            'id', 'document_type', 'document', 'description',
            'status', 'reviewer_notes', 'uploaded_at', 'reviewed_at'
        ]
        read_only_fields = ['id', 'status', 'reviewer_notes', 'uploaded_at', 'reviewed_at']


class SellerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sellers."""
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'business_name', 'business_type', 'logo',
            'city', 'state', 'is_verified', 'rating', 'total_reviews',
            'active_pet_count'
        ]


class SellerDashboardStatsSerializer(serializers.Serializer):
    """Serializer for seller dashboard statistics."""
    
    total_pets = serializers.IntegerField()
    available_pets = serializers.IntegerField()
    sold_pets = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
