from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "email" and "password".')
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for reading user data."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'role', 'avatar', 'is_verified',
            'is_superuser', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'is_superuser', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    user = UserSerializer(read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'address', 'city', 'state', 'country',
            'postal_code', 'date_of_birth', 'full_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user details."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'avatar']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = UserProfile
        fields = ['bio', 'address', 'city', 'state', 'country', 'postal_code', 'date_of_birth']


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SellerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for seller registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    # Seller profile fields
    business_name = serializers.CharField(max_length=200)
    business_type = serializers.ChoiceField(choices=[
        ('individual', 'Individual'),
        ('kennel', 'Kennel/Breeder'),
        ('shelter', 'Animal Shelter'),
        ('pet_shop', 'Pet Shop'),
    ])
    business_phone = serializers.CharField(max_length=20)
    business_address = serializers.CharField()
    business_city = serializers.CharField(max_length=100)
    business_state = serializers.CharField(max_length=100)
    business_postal_code = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number',
            'business_name', 'business_type', 'business_phone',
            'business_address', 'business_city', 'business_state',
            'business_postal_code'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        from sellers.models import SellerProfile

        # Extract seller profile fields
        business_name = validated_data.pop('business_name')
        business_type = validated_data.pop('business_type')
        business_phone = validated_data.pop('business_phone')
        business_address = validated_data.pop('business_address')
        business_city = validated_data.pop('business_city')
        business_state = validated_data.pop('business_state')
        business_postal_code = validated_data.pop('business_postal_code')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Create user with seller role
        user = User.objects.create_user(password=password, role='seller', **validated_data)

        # Create seller profile
        SellerProfile.objects.create(
            user=user,
            business_name=business_name,
            business_type=business_type,
            phone=business_phone,
            address=business_address,
            city=business_city,
            state=business_state,
            postal_code=business_postal_code,
        )

        return user
