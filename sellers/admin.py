from django.contrib import admin
from .models import SellerProfile, SellerVerificationDocument


class VerificationDocumentInline(admin.TabularInline):
    model = SellerVerificationDocument
    extra = 0
    readonly_fields = ['uploaded_at', 'reviewed_at']


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'user', 'business_type', 'city',
        'is_verified', 'total_pets_listed', 'rating', 'total_sales', 'joined_at'
    ]
    list_filter = ['is_verified', 'is_active', 'business_type', 'state']
    search_fields = ['business_name', 'user__email', 'city']
    raw_id_fields = ['user']
    inlines = [VerificationDocumentInline]
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Business Info', {
            'fields': ('business_name', 'business_type', 'registration_number', 'description', 'logo', 'website')
        }),
        ('Contact', {
            'fields': ('phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'verification_date')
        }),
        ('Stats', {
            'fields': ('rating', 'total_reviews', 'total_sales', 'total_pets_listed'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_sellers', 'unverify_sellers', 'recalculate_stats']
    
    def verify_sellers(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_verified=True, verification_date=timezone.now())
        self.message_user(request, f'{queryset.count()} seller(s) verified.')
    verify_sellers.short_description = 'Verify selected sellers'
    
    def unverify_sellers(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f'{queryset.count()} seller(s) unverified.')
    unverify_sellers.short_description = 'Unverify selected sellers'

    def recalculate_stats(self, request, queryset):
        for seller in queryset:
            seller.update_stats()
        self.message_user(request, f'Stats recalculated for {queryset.count()} seller(s).')
    recalculate_stats.short_description = 'Recalculate statistics for selected sellers'


@admin.register(SellerVerificationDocument)
class SellerVerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ['seller', 'document_type', 'status', 'uploaded_at', 'reviewed_at']
    list_filter = ['document_type', 'status']
    search_fields = ['seller__business_name']
    raw_id_fields = ['seller', 'reviewed_by']
    
    actions = ['approve_documents', 'reject_documents']
    
    def approve_documents(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} document(s) approved.')
    approve_documents.short_description = 'Approve selected documents'
    
    def reject_documents(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='rejected', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} document(s) rejected.')
    reject_documents.short_description = 'Reject selected documents'
