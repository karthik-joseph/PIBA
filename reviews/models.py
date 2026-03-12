from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class PetReview(models.Model):
    """Review for a purchased/adopted pet."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pet_reviews'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pet_reviews',
        help_text='Order that verified this purchase'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    body = models.TextField()

    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pet_reviews'
        verbose_name = 'Pet Review'
        verbose_name_plural = 'Pet Reviews'
        ordering = ['-created_at']
        unique_together = ['pet', 'reviewer']

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.pet.name}"

    def save(self, *args, **kwargs):
        # Auto-verify if linked to an order
        if self.order and self.order.buyer == self.reviewer:
            self.is_verified_purchase = True
        super().save(*args, **kwargs)


class SellerReview(models.Model):
    """Review for a seller."""

    seller = models.ForeignKey(
        'sellers.SellerProfile',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_reviews'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seller_reviews',
        help_text='Order that verified this transaction'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    body = models.TextField()

    # Review aspects
    communication_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    responsiveness_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    accuracy_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='How accurate was the pet listing description'
    )

    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seller_reviews'
        verbose_name = 'Seller Review'
        verbose_name_plural = 'Seller Reviews'
        ordering = ['-created_at']
        unique_together = ['seller', 'reviewer']

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.seller.business_name}"

    def save(self, *args, **kwargs):
        # Auto-verify if linked to an order
        if self.order and self.order.buyer == self.reviewer and self.order.seller == self.seller:
            self.is_verified_purchase = True
        super().save(*args, **kwargs)
        # Update seller stats
        self.seller.update_stats()


class ReviewResponse(models.Model):
    """Response to a review by the seller."""

    REVIEW_TYPE_CHOICES = [
        ('pet', 'Pet Review'),
        ('seller', 'Seller Review'),
    ]

    review_type = models.CharField(max_length=10, choices=REVIEW_TYPE_CHOICES)
    pet_review = models.OneToOneField(
        PetReview,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='response'
    )
    seller_review = models.OneToOneField(
        SellerReview,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='response'
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_responses'
    )
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_responses'
        verbose_name = 'Review Response'
        verbose_name_plural = 'Review Responses'

    def __str__(self):
        if self.pet_review:
            return f"Response to pet review by {self.pet_review.reviewer.username}"
        elif self.seller_review:
            return f"Response to seller review by {self.seller_review.reviewer.username}"
        return f"Review Response #{self.pk}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.review_type == 'pet' and not self.pet_review:
            raise ValidationError('Pet review is required for pet review type')
        if self.review_type == 'seller' and not self.seller_review:
            raise ValidationError('Seller review is required for seller review type')
