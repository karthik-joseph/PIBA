from rest_framework import serializers
from .models import PetReview, SellerReview, ReviewResponse


class PetReviewSerializer(serializers.ModelSerializer):
    """Serializer for pet reviews."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_avatar = serializers.ImageField(source='reviewer.avatar', read_only=True)
    response = serializers.SerializerMethodField()
    
    class Meta:
        model = PetReview
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar', 'rating', 'title', 'body',
            'is_verified_purchase', 'response', 'created_at'
        ]
    
    def get_response(self, obj):
        if hasattr(obj, 'response') and obj.response:
            return ReviewResponseSerializer(obj.response).data
        return None


class PetReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating pet reviews."""
    
    class Meta:
        model = PetReview
        fields = ['rating', 'title', 'body']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class SellerReviewSerializer(serializers.ModelSerializer):
    """Serializer for seller reviews."""
    
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_avatar = serializers.ImageField(source='reviewer.avatar', read_only=True)
    response = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerReview
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar', 'rating', 'title', 'body',
            'communication_rating', 'responsiveness_rating', 'accuracy_rating',
            'is_verified_purchase', 'response', 'created_at'
        ]
    
    def get_response(self, obj):
        if hasattr(obj, 'response') and obj.response:
            return ReviewResponseSerializer(obj.response).data
        return None


class SellerReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating seller reviews."""
    
    class Meta:
        model = SellerReview
        fields = [
            'rating', 'title', 'body',
            'communication_rating', 'responsiveness_rating', 'accuracy_rating'
        ]


class ReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for review responses."""
    
    responder_name = serializers.CharField(source='responder.get_full_name', read_only=True)
    
    class Meta:
        model = ReviewResponse
        fields = ['id', 'responder_name', 'response_text', 'created_at']


class ReviewResponseCreateSerializer(serializers.Serializer):
    """Serializer for creating review responses."""
    
    review_type = serializers.ChoiceField(choices=['pet', 'seller'])
    response_text = serializers.CharField()
