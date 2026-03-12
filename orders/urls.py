from django.urls import path
from . import views

urlpatterns = [
    # Cart API Endpoints
    path('api/v1/cart/', views.CartAPIView.as_view(), name='api_cart'),
    path('api/v1/cart/add/', views.AddToCartAPIView.as_view(), name='api_cart_add'),
    path('api/v1/cart/remove/<int:item_id>/', views.RemoveFromCartAPIView.as_view(), name='api_cart_remove'),
    path('api/v1/cart/clear/', views.ClearCartAPIView.as_view(), name='api_cart_clear'),

    # Checkout & Orders API
    path('api/v1/checkout/', views.CheckoutAPIView.as_view(), name='api_checkout'),
    path('api/v1/orders/', views.OrderListAPIView.as_view(), name='api_order_list'),
    path('api/v1/orders/<str:order_number>/', views.OrderDetailAPIView.as_view(), name='api_order_detail'),
    path('api/v1/orders/<str:order_number>/cancel/', views.OrderCancelAPIView.as_view(), name='api_order_cancel'),
    
    # Seller Order Management
    path('api/v1/orders/seller/', views.SellerOrderListAPIView.as_view(), name='api_seller_orders'),
    path('api/v1/orders/seller/<str:order_number>/update/', views.SellerOrderUpdateAPIView.as_view(), name='api_seller_order_update'),

    # Mock Payment API
    path('api/v1/payments/initiate/', views.MockPaymentInitAPIView.as_view(), name='api_payment_init'),
    path('api/v1/payments/callback/', views.MockPaymentCallbackAPIView.as_view(), name='api_payment_callback'),
    path('api/v1/payments/<str:order_number>/status/', views.PaymentStatusAPIView.as_view(), name='api_payment_status'),

    # Template Views
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/<str:order_number>/', views.PaymentView.as_view(), name='payment'),
    path('order/confirmation/<str:order_number>/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
]
