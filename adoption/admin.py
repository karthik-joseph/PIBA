from django.contrib import admin
from .models import AdoptionRequest, AdoptionFollowUp


class AdoptionFollowUpInline(admin.TabularInline):
    model = AdoptionFollowUp
    extra = 0
    raw_id_fields = ['conducted_by']


@admin.register(AdoptionRequest)
class AdoptionRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'pet', 'applicant', 'status', 'living_situation',
        'experience_level', 'submitted_at'
    ]
    list_filter = ['status', 'living_situation', 'experience_level', 'submitted_at']
    search_fields = ['pet__name', 'applicant__email', 'reason']
    raw_id_fields = ['pet', 'applicant']
    readonly_fields = ['submitted_at', 'reviewed_at', 'completed_at']
    inlines = [AdoptionFollowUpInline]
    
    fieldsets = (
        ('Request Info', {
            'fields': ('pet', 'applicant', 'status')
        }),
        ('Application', {
            'fields': ('reason', 'living_situation', 'living_situation_details')
        }),
        ('Household', {
            'fields': (
                'has_other_pets', 'other_pets_description',
                'has_children', 'children_ages', 'household_members'
            )
        }),
        ('Experience', {
            'fields': (
                'experience_level', 'experience_description',
                'daily_hours_alone', 'veterinarian_name', 'veterinarian_phone'
            )
        }),
        ('References & Agreements', {
            'fields': (
                'references', 'agrees_to_home_visit',
                'agrees_to_followup', 'agrees_to_return_policy'
            ),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': ('reviewer_notes', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'reviewed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_under_review', 'approve_requests', 'reject_requests']
    
    def mark_under_review(self, request, queryset):
        queryset.filter(status='pending').update(status='under_review')
        self.message_user(request, 'Requests marked as under review.')
    mark_under_review.short_description = 'Mark as Under Review'
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        for req in queryset.filter(status__in=['pending', 'under_review']):
            req.status = 'approved'
            req.reviewed_at = timezone.now()
            req.save()
            req.pet.status = 'reserved'
            req.pet.save()
        self.message_user(request, 'Requests approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status__in=['pending', 'under_review']).update(
            status='rejected',
            reviewed_at=timezone.now()
        )
        self.message_user(request, 'Requests rejected.')
    reject_requests.short_description = 'Reject selected requests'


@admin.register(AdoptionFollowUp)
class AdoptionFollowUpAdmin(admin.ModelAdmin):
    list_display = ['adoption_request', 'scheduled_date', 'status', 'conducted_by']
    list_filter = ['status', 'scheduled_date']
    raw_id_fields = ['adoption_request', 'conducted_by']
