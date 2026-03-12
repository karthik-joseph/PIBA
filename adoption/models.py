from django.db import models
from django.conf import settings


class AdoptionRequest(models.Model):
    """Adoption request submitted by a potential adopter."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    ]

    LIVING_SITUATION_CHOICES = [
        ('house_with_yard', 'House with Yard'),
        ('house_no_yard', 'House without Yard'),
        ('apartment', 'Apartment'),
        ('farm', 'Farm/Rural Property'),
        ('other', 'Other'),
    ]

    EXPERIENCE_CHOICES = [
        ('first_time', 'First-time Pet Owner'),
        ('some', 'Some Experience'),
        ('experienced', 'Experienced Pet Owner'),
        ('professional', 'Professional/Breeder'),
    ]

    # Relationships
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='adoption_requests'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adoption_requests'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Application Details
    reason = models.TextField(help_text='Why do you want to adopt this pet?')
    living_situation = models.CharField(max_length=20, choices=LIVING_SITUATION_CHOICES)
    living_situation_details = models.TextField(blank=True, help_text='Please describe your living situation')

    # Household Info
    has_other_pets = models.BooleanField(default=False)
    other_pets_description = models.TextField(blank=True)
    has_children = models.BooleanField(default=False)
    children_ages = models.CharField(max_length=100, blank=True, help_text='Ages of children in household')
    household_members = models.PositiveSmallIntegerField(default=1, help_text='Number of people in household')

    # Experience & Commitment
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='some')
    experience_description = models.TextField(blank=True, help_text='Describe your experience with pets')
    daily_hours_alone = models.PositiveSmallIntegerField(default=0, help_text='Hours pet will be alone daily')
    veterinarian_name = models.CharField(max_length=200, blank=True)
    veterinarian_phone = models.CharField(max_length=20, blank=True)

    # References (stored as JSON array)
    references = models.JSONField(default=list, blank=True)

    # Agreement
    agrees_to_home_visit = models.BooleanField(default=False)
    agrees_to_followup = models.BooleanField(default=False)
    agrees_to_return_policy = models.BooleanField(default=False)

    # Review Info
    reviewer_notes = models.TextField(blank=True, help_text='Internal notes for review')
    rejection_reason = models.TextField(blank=True, help_text='Reason shown to applicant if rejected')

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'adoption_requests'
        verbose_name = 'Adoption Request'
        verbose_name_plural = 'Adoption Requests'
        ordering = ['-submitted_at']
        unique_together = ['pet', 'applicant']

    def __str__(self):
        return f"Adoption Request: {self.applicant.username} for {self.pet.name}"

    @property
    def can_be_approved(self):
        """Check if request can be approved."""
        return (
            self.status in ['pending', 'under_review'] and
            self.pet.status == 'available' and
            self.pet.listing_type == 'adoption'
        )


class AdoptionFollowUp(models.Model):
    """Follow-up records after adoption approval."""

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('rescheduled', 'Rescheduled'),
    ]

    adoption_request = models.ForeignKey(
        AdoptionRequest,
        on_delete=models.CASCADE,
        related_name='follow_ups'
    )
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    method = models.CharField(max_length=50, blank=True, help_text='Phone call, home visit, etc.')
    notes = models.TextField(blank=True)
    pet_condition = models.CharField(max_length=100, blank=True, help_text='How is the pet doing?')
    concerns = models.TextField(blank=True)
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_followups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'adoption_follow_ups'
        verbose_name = 'Adoption Follow-Up'
        verbose_name_plural = 'Adoption Follow-Ups'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"Follow-up for {self.adoption_request} on {self.scheduled_date}"
