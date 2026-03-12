import django_filters
from .models import Pet, PetCategory, Breed


class PetFilter(django_filters.FilterSet):
    """Filter for pet listings."""
    
    # Price range
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Age range (in months, converted)
    min_age = django_filters.NumberFilter(method='filter_min_age')
    max_age = django_filters.NumberFilter(method='filter_max_age')
    
    # Category and breed
    category = django_filters.CharFilter(field_name='category__slug')
    breed = django_filters.CharFilter(field_name='breed__slug')
    
    # Location
    city = django_filters.CharFilter(field_name='seller__city', lookup_expr='icontains')
    state = django_filters.CharFilter(field_name='seller__state', lookup_expr='icontains')
    
    # Boolean filters
    is_vaccinated = django_filters.BooleanFilter()
    is_neutered = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    
    # Choice filters
    gender = django_filters.ChoiceFilter(choices=Pet.GENDER_CHOICES)
    listing_type = django_filters.ChoiceFilter(choices=Pet.LISTING_TYPE_CHOICES)
    health_status = django_filters.ChoiceFilter(choices=Pet.HEALTH_STATUS_CHOICES)
    
    # Search
    search = django_filters.CharFilter(method='filter_search')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('created_at', 'date'),
            ('created_at', 'created_at'),
            ('views_count', 'views'),
            ('views_count', 'views_count'),
            ('name', 'name'),
        ),
        field_labels={
            'price': 'Price',
            '-price': 'Price (High to Low)',
            'created_at': 'Date',
            '-created_at': 'Newest First',
            'date': 'Date',
            '-date': 'Newest First',
            'views_count': 'Most Viewed',
            '-views_count': 'Most Viewed',
        }
    )
    
    class Meta:
        model = Pet
        fields = [
            'category', 'breed', 'gender', 'listing_type',
            'health_status', 'is_vaccinated', 'is_neutered', 'is_featured'
        ]
    
    def filter_min_age(self, queryset, name, value):
        """Filter by minimum age (in months)."""
        if value is not None:
            # Convert months to years and months
            years = value // 12
            months = value % 12
            return queryset.filter(
                models.Q(age_years__gt=years) |
                models.Q(age_years=years, age_months__gte=months)
            )
        return queryset
    
    def filter_max_age(self, queryset, name, value):
        """Filter by maximum age (in months)."""
        if value is not None:
            years = value // 12
            months = value % 12
            return queryset.filter(
                models.Q(age_years__lt=years) |
                models.Q(age_years=years, age_months__lte=months)
            )
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if value:
            return queryset.filter(
                models.Q(name__icontains=value) |
                models.Q(description__icontains=value) |
                models.Q(breed__name__icontains=value) |
                models.Q(category__name__icontains=value) |
                models.Q(color__icontains=value)
            )
        return queryset


# Import models for Q objects
from django.db import models
