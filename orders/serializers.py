from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, MockPayment
from pets.serializers import PetListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items."""
    
    pet = PetListSerializer(read_only=True)
    pet_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'pet', 'pet_id', 'added_at']
        read_only_fields = ['id', 'added_at']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart."""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'subtotal', 'tax_amount', 'total', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    
    pet_slug = serializers.CharField(source='pet.slug', read_only=True)
    pet_primary_image = serializers.CharField(source='pet.primary_image_url', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'pet', 'pet_slug', 'pet_primary_image',
            'price_at_purchase', 'pet_name_snapshot',
            'pet_breed_snapshot', 'pet_category_snapshot'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order list."""
    
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'total_amount',
            'seller_name', 'items_count', 'items', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for order."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    shipping_address_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'buyer_email', 'buyer_name',
            'seller_name', 'seller_phone',
            'status', 'payment_status', 'payment_method',
            'subtotal', 'tax_amount', 'shipping_amount', 'total_amount',
            'shipping_address', 'shipping_address_display',
            'buyer_notes', 'admin_notes', 'items',
            'created_at', 'confirmed_at', 'shipped_at', 'delivered_at'
        ]


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process."""
    
    shipping_address = serializers.CharField()
    shipping_city = serializers.CharField()
    shipping_state = serializers.CharField()
    shipping_postal_code = serializers.CharField()
    shipping_country = serializers.CharField(default='India')
    payment_method = serializers.ChoiceField(choices=[
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('cod', 'Cash on Delivery'),
    ])
    buyer_notes = serializers.CharField(required=False, allow_blank=True)


class MockPaymentSerializer(serializers.ModelSerializer):
    """Serializer for mock payment."""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = MockPayment
        fields = [
            'id', 'order_number', 'payment_gateway', 'amount',
            'currency', 'status', 'mock_payment_id', 'created_at'
        ]


class PaymentInitSerializer(serializers.Serializer):
    """Serializer for initiating payment."""
    
    order_number = serializers.CharField()


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for payment callback."""
    
    order_number = serializers.CharField()
    status = serializers.ChoiceField(choices=['success', 'failed'])
    transaction_id = serializers.CharField(required=False, allow_blank=True)
