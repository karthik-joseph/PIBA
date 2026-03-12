from django.contrib import admin
from .models import PetCategory, Breed, Pet, PetImage, PetHealthRecord


class PetImageInline(admin.TabularInline):
    model = PetImage
    extra = 1


class PetHealthRecordInline(admin.TabularInline):
    model = PetHealthRecord
    extra = 0


@admin.register(PetCategory)
class PetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'display_order', 'pet_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    
    def pet_count(self, obj):
        return obj.pets.filter(status='available', is_approved=True).count()
    pet_count.short_description = 'Available Pets'


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'average_size', 'is_active']
    list_filter = ['category', 'average_size', 'is_active']
    search_fields = ['name', 'description', 'temperament']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'name']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'breed', 'seller', 'price', 'status',
        'listing_type', 'is_approved', 'is_featured', 'created_at'
    ]
    list_filter = [
        'status', 'listing_type', 'category', 'is_approved',
        'is_featured', 'is_vaccinated', 'gender', 'health_status'
    ]
    search_fields = ['name', 'description', 'seller__business_name']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['seller', 'breed']
    inlines = [PetImageInline, PetHealthRecordInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('seller', 'category', 'breed', 'name', 'slug')
        }),
        ('Details', {
            'fields': ('age_years', 'age_months', 'gender', 'color', 'weight', 'description')
        }),
        ('Health', {
            'fields': ('health_status', 'is_vaccinated', 'is_neutered', 'health_certificate')
        }),
        ('Listing', {
            'fields': ('price', 'listing_type', 'status')
        }),
        ('Flags', {
            'fields': ('is_featured', 'is_approved', 'is_active')
        }),
        ('Stats', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_pets', 'feature_pets', 'unfeature_pets']
    
    def approve_pets(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} pet(s) approved.')
    approve_pets.short_description = 'Approve selected pets'
    
    def feature_pets(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} pet(s) featured.')
    feature_pets.short_description = 'Feature selected pets'
    
    def unfeature_pets(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'{queryset.count()} pet(s) unfeatured.')
    unfeature_pets.short_description = 'Unfeature selected pets'


@admin.register(PetImage)
class PetImageAdmin(admin.ModelAdmin):
    list_display = ['pet', 'is_primary', 'display_order', 'created_at']
    list_filter = ['is_primary']
    raw_id_fields = ['pet']


@admin.register(PetHealthRecord)
class PetHealthRecordAdmin(admin.ModelAdmin):
    list_display = ['pet', 'record_type', 'title', 'date']
    list_filter = ['record_type']
    search_fields = ['pet__name', 'title', 'description']
    raw_id_fields = ['pet']
