from django.db import models
from django.conf import settings


class SellerProfile(models.Model):
    """Profile for sellers/vendors on the platform."""

    BUSINESS_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('kennel', 'Kennel/Breeder'),
        ('shelter', 'Animal Shelter'),
        ('pet_shop', 'Pet Shop'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='individual')
    registration_number = models.CharField(max_length=100, blank=True, help_text='Business registration/license number')
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='seller_logos/', blank=True, null=True)
    website = models.URLField(blank=True)

    # Contact & Location
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)

    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    verification_date = models.DateTimeField(null=True, blank=True)

    # Stats (cached for performance)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_sales = models.PositiveIntegerField(default=0)
    total_pets_listed = models.PositiveIntegerField(default=0)

    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seller_profiles'
        verbose_name = 'Seller Profile'
        verbose_name_plural = 'Seller Profiles'
        ordering = ['-joined_at']

    def __str__(self):
        return self.business_name

    @property
    def active_pet_count(self):
        """Return count of active, available pets."""
        return self.pets.filter(status='available', is_approved=True, is_active=True).count()

    def get_full_address(self):
        """Return formatted full address."""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(part for part in parts if part)

    def update_stats(self):
        """Update cached statistics."""
        from reviews.models import SellerReview
        from orders.models import Order

        reviews = SellerReview.objects.filter(seller=self, is_approved=True)
        self.total_reviews = reviews.count()
        if self.total_reviews > 0:
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2) if avg_rating else 0

        self.total_sales = Order.objects.filter(
            seller=self,
            status='delivered',
            payment_status='paid'
        ).count()

        self.total_pets_listed = self.pets.filter(is_active=True).count()
        self.save(update_fields=['rating', 'total_reviews', 'total_sales', 'total_pets_listed'])


class SellerVerificationDocument(models.Model):
    """Documents submitted by sellers for verification."""

    DOCUMENT_TYPE_CHOICES = [
        ('id_proof', 'ID Proof'),
        ('business_license', 'Business License'),
        ('health_cert', 'Health Certificate'),
        ('address_proof', 'Address Proof'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='verification_documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document = models.FileField(upload_to='seller_documents/')
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents'
    )

    class Meta:
        db_table = 'seller_verification_documents'
        verbose_name = 'Seller Verification Document'
        verbose_name_plural = 'Seller Verification Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.seller.business_name}"
