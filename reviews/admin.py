from django.contrib import admin
from .models import PetReview, SellerReview, ReviewResponse


@admin.register(PetReview)
class PetReviewAdmin(admin.ModelAdmin):
    list_display = ['pet', 'reviewer', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['pet__name', 'reviewer__email', 'title', 'body']
    raw_id_fields = ['pet', 'reviewer', 'order']
    
    actions = ['approve_reviews', 'reject_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} review(s) approved.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} review(s) rejected.')
    reject_reviews.short_description = 'Reject selected reviews'


@admin.register(SellerReview)
class SellerReviewAdmin(admin.ModelAdmin):
    list_display = ['seller', 'reviewer', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['seller__business_name', 'reviewer__email', 'title', 'body']
    raw_id_fields = ['seller', 'reviewer', 'order']
    
    actions = ['approve_reviews', 'reject_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} review(s) approved.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} review(s) rejected.')
    reject_reviews.short_description = 'Reject selected reviews'


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ['review_type', 'responder', 'created_at']
    list_filter = ['review_type', 'created_at']
    raw_id_fields = ['pet_review', 'seller_review', 'responder']
