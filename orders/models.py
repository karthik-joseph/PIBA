from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


def generate_order_number():
    """Generate a unique order number."""
    year = timezone.now().year
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"PIBA-{year}-{unique_id}"


class Cart(models.Model):
    """Shopping cart for users."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=255, blank=True, help_text='For guest users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Guest Cart ({self.session_key[:8]}...)"

    @property
    def total_items(self):
        """Return total number of items in cart."""
        return self.items.count()

    @property
    def subtotal(self):
        """Calculate cart subtotal."""
        return sum(item.pet.price for item in self.items.all())

    @property
    def tax_amount(self):
        """Calculate tax (18% GST)."""
        return round(self.subtotal * Decimal('0.18'), 2)

    @property
    def total(self):
        """Calculate cart total including tax."""
        return self.subtotal + self.tax_amount

    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual item in a shopping cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'pet']

    def __str__(self):
        return f"{self.pet.name} in {self.cart}"


class Order(models.Model):
    """Order placed by a buyer."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('cod', 'Cash on Delivery'),
        ('mock_card', 'Credit/Debit Card (Legacy)'),
        ('mock_upi', 'UPI (Legacy)'),
        ('mock_netbanking', 'Net Banking (Legacy)'),
        ('mock_cod', 'Cash on Delivery (Legacy)'),
    ]

    order_number = models.CharField(max_length=50, unique=True, default=generate_order_number)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    seller = models.ForeignKey(
        'sellers.SellerProfile',
        on_delete=models.PROTECT,
        related_name='orders'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_transaction_id = models.CharField(max_length=255, blank=True)

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Shipping Address (snapshot)
    shipping_address = models.JSONField(default=dict)

    # Notes
    buyer_notes = models.TextField(blank=True)
    seller_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        # Auto-set timestamps based on status changes
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == 'shipped' and not self.shipped_at:
            self.shipped_at = timezone.now()
        elif self.status == 'delivered' and not self.delivered_at:
            self.delivered_at = timezone.now()
        elif self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def shipping_address_display(self):
        """Return formatted shipping address."""
        addr = self.shipping_address
        if not addr:
            return 'No address provided'
        parts = [
            addr.get('address', ''),
            addr.get('city', ''),
            addr.get('state', ''),
            addr.get('postal_code', ''),
            addr.get('country', '')
        ]
        return ', '.join(part for part in parts if part)


class OrderItem(models.Model):
    """Individual pet in an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    # Snapshot at time of purchase
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    pet_name_snapshot = models.CharField(max_length=150)
    pet_breed_snapshot = models.CharField(max_length=150, blank=True)
    pet_category_snapshot = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.pet_name_snapshot} in Order {self.order.order_number}"


class MockPayment(models.Model):
    """Mock payment record for simulated payments."""

    GATEWAY_CHOICES = [
        ('mock_razorpay', 'Razorpay (Mock)'),
        ('mock_stripe', 'Stripe (Mock)'),
    ]

    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, default='mock_razorpay')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    mock_payment_id = models.CharField(max_length=100, blank=True)
    mock_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mock_payments'
        verbose_name = 'Mock Payment'
        verbose_name_plural = 'Mock Payments'

    def __str__(self):
        return f"Payment for {self.order.order_number}"

    def simulate_success(self):
        """Simulate a successful payment."""
        self.status = 'success'
        self.mock_payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        self.mock_response = {
            'status': 'success',
            'payment_id': self.mock_payment_id,
            'amount': str(self.amount),
            'currency': self.currency,
            'timestamp': timezone.now().isoformat(),
        }
        self.save()
        # Update order payment status
        self.order.payment_status = 'paid'
        self.order.payment_transaction_id = self.mock_payment_id
        self.order.save()
        return True

    def simulate_failure(self, reason='Payment declined'):
        """Simulate a failed payment."""
        self.status = 'failed'
        self.mock_response = {
            'status': 'failed',
            'error': reason,
            'timestamp': timezone.now().isoformat(),
        }
        self.save()
        self.order.payment_status = 'failed'
        self.order.save()
        return False
