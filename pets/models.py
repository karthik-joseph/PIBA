from django.db import models
from django.utils.text import slugify
from django.conf import settings


class PetCategory(models.Model):
    """Categories for pets (Dogs, Cats, Birds, Fish, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=255, blank=True, help_text='Icon filename from static/images/icons/pet_category/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pet_categories'
        verbose_name = 'Pet Category'
        verbose_name_plural = 'Pet Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Breed(models.Model):
    """Breeds within each pet category."""

    SIZE_CHOICES = [
        ('tiny', 'Tiny'),
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large'),
    ]

    category = models.ForeignKey(
        PetCategory,
        on_delete=models.CASCADE,
        related_name='breeds'
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    average_lifespan = models.CharField(max_length=50, blank=True, help_text='e.g., 10-15 years')
    average_size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='medium')
    temperament = models.TextField(blank=True, help_text='General temperament traits')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'breeds'
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'
        ordering = ['category', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Pet(models.Model):
    """Main pet listing model."""

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unknown', 'Unknown'),
    ]

    HEALTH_STATUS_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('adopted', 'Adopted'),
    ]

    LISTING_TYPE_CHOICES = [
        ('sale', 'For Sale'),
        ('adoption', 'For Adoption'),
    ]

    # Relationships
    seller = models.ForeignKey(
        'sellers.SellerProfile',
        on_delete=models.CASCADE,
        related_name='pets'
    )
    category = models.ForeignKey(
        PetCategory,
        on_delete=models.PROTECT,
        related_name='pets'
    )
    breed = models.ForeignKey(
        Breed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pets'
    )

    # Basic Info
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    age_years = models.PositiveSmallIntegerField(default=0)
    age_months = models.PositiveSmallIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown')
    color = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Weight in kg')
    description = models.TextField(blank=True)

    # Health
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='good')
    is_vaccinated = models.BooleanField(default=False)
    is_neutered = models.BooleanField(default=False)
    health_certificate = models.FileField(upload_to='health_certificates/', blank=True, null=True)

    # Listing Details
    price = models.DecimalField(max_digits=10, decimal_places=2)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='sale')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    # Flags
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Stats
    views_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pets'
        verbose_name = 'Pet'
        verbose_name_plural = 'Pets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.breed or self.category}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.category.name}")
            slug = base_slug
            counter = 1
            while Pet.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def age_display(self):
        """Return formatted age string."""
        parts = []
        if self.age_years:
            parts.append(f"{self.age_years} year{'s' if self.age_years > 1 else ''}")
        if self.age_months:
            parts.append(f"{self.age_months} month{'s' if self.age_months > 1 else ''}")
        return ' '.join(parts) if parts else 'Unknown'

    @property
    def primary_image(self):
        """Return the primary image or first image."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def primary_image_url(self):
        """Return URL of primary image or placeholder."""
        img = self.primary_image
        if img and img.image:
            return img.image.url
        return '/static/images/placeholder/default_pet_image.png'

    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class PetImage(models.Model):
    """Images for pet listings."""

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='pet_images/')
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pet_images'
        verbose_name = 'Pet Image'
        verbose_name_plural = 'Pet Images'
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"Image for {self.pet.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per pet
        if self.is_primary:
            PetImage.objects.filter(pet=self.pet, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class PetHealthRecord(models.Model):
    """Health records for pets."""

    RECORD_TYPE_CHOICES = [
        ('vaccination', 'Vaccination'),
        ('checkup', 'Health Checkup'),
        ('surgery', 'Surgery'),
        ('treatment', 'Treatment'),
        ('other', 'Other'),
    ]

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='health_records'
    )
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    veterinarian_name = models.CharField(max_length=200, blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    document = models.FileField(upload_to='health_records/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pet_health_records'
        verbose_name = 'Pet Health Record'
        verbose_name_plural = 'Pet Health Records'
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.pet.name}"
