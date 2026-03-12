from rest_framework import serializers
from .models import AdoptionRequest, AdoptionFollowUp


class AdoptionRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating adoption requests."""
    
    pet_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AdoptionRequest
        fields = [
            'pet_id', 'reason', 'living_situation', 'living_situation_details',
            'has_other_pets', 'other_pets_description', 'has_children', 'children_ages',
            'household_members', 'experience_level', 'experience_description',
            'daily_hours_alone', 'veterinarian_name', 'veterinarian_phone',
            'references', 'agrees_to_home_visit', 'agrees_to_followup', 'agrees_to_return_policy'
        ]


class AdoptionRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing adoption requests."""
    
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    pet_slug = serializers.CharField(source='pet.slug', read_only=True)
    pet_image = serializers.CharField(source='pet.primary_image_url', read_only=True)
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    
    class Meta:
        model = AdoptionRequest
        fields = [
            'id', 'pet_name', 'pet_slug', 'pet_image', 'applicant_name',
            'status', 'submitted_at'
        ]


class AdoptionRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for adoption request."""
    
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    pet_slug = serializers.CharField(source='pet.slug', read_only=True)
    pet_category = serializers.CharField(source='pet.category.name', read_only=True)
    pet_breed = serializers.CharField(source='pet.breed.name', read_only=True, allow_null=True)
    pet_image = serializers.CharField(source='pet.primary_image_url', read_only=True)
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    applicant_email = serializers.CharField(source='applicant.email', read_only=True)
    applicant_phone = serializers.CharField(source='applicant.phone_number', read_only=True)
    follow_ups = serializers.SerializerMethodField()
    
    class Meta:
        model = AdoptionRequest
        fields = [
            'id', 'pet', 'pet_name', 'pet_slug', 'pet_category', 'pet_breed', 'pet_image',
            'applicant', 'applicant_name', 'applicant_email', 'applicant_phone',
            'status', 'reason', 'living_situation', 'living_situation_details',
            'has_other_pets', 'other_pets_description', 'has_children', 'children_ages',
            'household_members', 'experience_level', 'experience_description',
            'daily_hours_alone', 'veterinarian_name', 'veterinarian_phone',
            'references', 'agrees_to_home_visit', 'agrees_to_followup', 'agrees_to_return_policy',
            'reviewer_notes', 'rejection_reason', 'follow_ups',
            'submitted_at', 'reviewed_at', 'completed_at'
        ]
    
    def get_follow_ups(self, obj):
        follow_ups = obj.follow_ups.all()
        return AdoptionFollowUpSerializer(follow_ups, many=True).data


class AdoptionRequestUpdateSerializer(serializers.Serializer):
    """Serializer for updating adoption request status."""
    
    status = serializers.ChoiceField(choices=[
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ])
    reviewer_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class AdoptionFollowUpSerializer(serializers.ModelSerializer):
    """Serializer for adoption follow-ups."""
    
    conducted_by_name = serializers.CharField(source='conducted_by.get_full_name', read_only=True)
    
    class Meta:
        model = AdoptionFollowUp
        fields = [
            'id', 'scheduled_date', 'actual_date', 'status', 'method',
            'notes', 'pet_condition', 'concerns', 'conducted_by_name', 'created_at'
        ]


class AdoptionFollowUpCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating follow-ups."""
    
    adoption_request_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AdoptionFollowUp
        fields = [
            'adoption_request_id', 'scheduled_date', 'method', 'notes'
        ]
