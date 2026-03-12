from rest_framework import serializers
from .models import PetCategory, Breed, Pet, PetImage, PetHealthRecord


class PetCategorySerializer(serializers.ModelSerializer):
    """Serializer for pet categories."""
    
    pet_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PetCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'is_active', 'pet_count']


class BreedSerializer(serializers.ModelSerializer):
    """Serializer for pet breeds."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Breed
        fields = [
            'id', 'name', 'slug', 'category', 'category_name',
            'description', 'average_lifespan', 'average_size', 'temperament'
        ]


class PetImageSerializer(serializers.ModelSerializer):
    """Serializer for pet images."""
    
    class Meta:
        model = PetImage
        fields = ['id', 'image', 'is_primary', 'display_order']


class PetHealthRecordSerializer(serializers.ModelSerializer):
    """Serializer for pet health records."""
    
    class Meta:
        model = PetHealthRecord
        fields = [
            'id', 'record_type', 'title', 'description', 'date',
            'veterinarian_name', 'clinic_name', 'document'
        ]


class PetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for pet listings."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    breed_name = serializers.CharField(source='breed.name', read_only=True, allow_null=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    seller_city = serializers.CharField(source='seller.city', read_only=True)
    primary_image_url = serializers.CharField(read_only=True)
    age_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'slug', 'category', 'category_name',
            'breed', 'breed_name', 'age_display', 'gender', 'price',
            'listing_type', 'status', 'is_vaccinated', 'is_featured',
            'primary_image_url', 'seller_name', 'seller_city',
            'views_count', 'created_at'
        ]


class PetDetailSerializer(serializers.ModelSerializer):
    """Full serializer for pet details."""
    
    category = PetCategorySerializer(read_only=True)
    breed = BreedSerializer(read_only=True, allow_null=True)
    images = PetImageSerializer(many=True, read_only=True)
    health_records = PetHealthRecordSerializer(many=True, read_only=True)
    age_display = serializers.CharField(read_only=True)
    primary_image_url = serializers.CharField(read_only=True)
    
    # Seller info
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    seller_city = serializers.CharField(source='seller.city', read_only=True)
    seller_rating = serializers.DecimalField(source='seller.rating', max_digits=3, decimal_places=2, read_only=True)
    seller_is_verified = serializers.BooleanField(source='seller.is_verified', read_only=True)
    
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'slug', 'category', 'breed',
            'age_years', 'age_months', 'age_display', 'gender', 'color', 'weight',
            'description', 'health_status', 'is_vaccinated', 'is_neutered',
            'health_certificate', 'price', 'listing_type', 'status',
            'is_featured', 'views_count', 'images', 'health_records',
            'primary_image_url', 'seller_id', 'seller_name', 'seller_city',
            'seller_rating', 'seller_is_verified', 'created_at', 'updated_at'
        ]


class PetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating pet listings."""
    
    class Meta:
        model = Pet
        fields = [
            'category', 'breed', 'name', 'age_years', 'age_months',
            'gender', 'color', 'weight', 'description',
            'health_status', 'is_vaccinated', 'is_neutered',
            'health_certificate', 'price', 'listing_type'
        ]

    def create(self, validated_data):
        # Seller is set from the request user
        request = self.context.get('request')
        if request and hasattr(request.user, 'seller_profile'):
            validated_data['seller'] = request.user.seller_profile
        return super().create(validated_data)


class PetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating pet listings."""
    
    class Meta:
        model = Pet
        fields = [
            'name', 'age_years', 'age_months', 'gender', 'color', 'weight',
            'description', 'health_status', 'is_vaccinated', 'is_neutered',
            'health_certificate', 'price', 'listing_type', 'status'
        ]


class PetImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading pet images."""
    
    class Meta:
        model = PetImage
        fields = ['image', 'is_primary', 'display_order']
