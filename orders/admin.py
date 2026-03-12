from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, MockPayment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ['pet']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_items', 'subtotal', 'updated_at']
    search_fields = ['user__email']
    raw_id_fields = ['user']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['pet']
    readonly_fields = ['price_at_purchase', 'pet_name_snapshot', 'pet_breed_snapshot', 'pet_category_snapshot']


class MockPaymentInline(admin.StackedInline):
    model = MockPayment
    extra = 0
    readonly_fields = ['mock_payment_id', 'mock_response', 'created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'buyer', 'seller', 'status',
        'payment_status', 'total_amount', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'buyer__email', 'seller__business_name']
    raw_id_fields = ['buyer', 'seller']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at']
    inlines = [OrderItemInline, MockPaymentInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'buyer', 'seller')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'payment_method', 'payment_transaction_id')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'shipping_amount', 'total_amount')
        }),
        ('Shipping', {
            'fields': ('shipping_address',)
        }),
        ('Notes', {
            'fields': ('buyer_notes', 'seller_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, 'Orders marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark as Confirmed'
    
    def mark_as_shipped(self, request, queryset):
        queryset.filter(status__in=['confirmed', 'processing']).update(status='shipped')
        self.message_user(request, 'Orders marked as shipped.')
    mark_as_shipped.short_description = 'Mark as Shipped'
    
    def mark_as_delivered(self, request, queryset):
        queryset.filter(status='shipped').update(status='delivered')
        self.message_user(request, 'Orders marked as delivered.')
    mark_as_delivered.short_description = 'Mark as Delivered'


@admin.register(MockPayment)
class MockPaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'status', 'payment_gateway', 'created_at']
    list_filter = ['status', 'payment_gateway']
    search_fields = ['order__order_number']
    raw_id_fields = ['order']
