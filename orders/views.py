from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db import transaction
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Cart, CartItem, Order, OrderItem, MockPayment
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    MockPaymentSerializer,
    PaymentInitSerializer,
    PaymentCallbackSerializer,
)
from pets.models import Pet
from users.permissions import IsSeller, IsAdmin


# ============ Cart API Views ============

class CartAPIView(APIView):
    """Get current user's cart."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartAPIView(APIView):
    """Add a pet to cart."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pet_id = request.data.get('pet_id')
        if not pet_id:
            return Response({'error': 'pet_id is required.'}, status=400)
        
        pet = get_object_or_404(Pet, id=pet_id)
        
        # Validate pet is available
        if pet.status != 'available':
            return Response({'error': 'This pet is no longer available.'}, status=400)
        if not pet.is_approved:
            return Response({'error': 'This pet listing is not approved.'}, status=400)
        if pet.listing_type != 'sale':
            return Response({'error': 'This pet is only available for adoption.'}, status=400)
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Check if already in cart
        if CartItem.objects.filter(cart=cart, pet=pet).exists():
            return Response({'error': 'This pet is already in your cart.'}, status=400)
        
        CartItem.objects.create(cart=cart, pet=pet)
        
        return Response({
            'message': 'Pet added to cart successfully.',
            'cart': CartSerializer(cart).data
        })


class RemoveFromCartAPIView(APIView):
    """Remove a pet from cart."""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        
        return Response({
            'message': 'Item removed from cart.',
            'cart': CartSerializer(cart).data
        })


class ClearCartAPIView(APIView):
    """Clear all items from cart."""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.clear()
        
        return Response({'message': 'Cart cleared successfully.'})


# ============ Order API Views ============

class CheckoutAPIView(APIView):
    """Process checkout and create order."""
    
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Your cart is empty.'}, status=400)
        
        # Verify all pets are still available
        for item in cart.items.all():
            if item.pet.status != 'available':
                return Response({
                    'error': f'{item.pet.name} is no longer available.'
                }, status=400)
        
        # Group items by seller
        sellers = {}
        for item in cart.items.all():
            seller = item.pet.seller
            if seller.id not in sellers:
                sellers[seller.id] = {'seller': seller, 'items': []}
            sellers[seller.id]['items'].append(item)
        
        orders_created = []
        
        # Create order for each seller
        for seller_id, seller_data in sellers.items():
            seller = seller_data['seller']
            items = seller_data['items']
            
            subtotal = sum(item.pet.price for item in items)
            tax_amount = round(subtotal * Decimal('0.18'), 2)  # 18% GST
            total_amount = subtotal + tax_amount
            
            order = Order.objects.create(
                buyer=request.user,
                seller=seller,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_method=data['payment_method'],
                shipping_address={
                    'address': data['shipping_address'],
                    'city': data['shipping_city'],
                    'state': data['shipping_state'],
                    'postal_code': data['shipping_postal_code'],
                    'country': data['shipping_country'],
                },
                buyer_notes=data.get('buyer_notes', ''),
            )
            
            # Create order items and update pet status
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    pet=item.pet,
                    price_at_purchase=item.pet.price,
                    pet_name_snapshot=item.pet.name,
                    pet_breed_snapshot=item.pet.breed.name if item.pet.breed else '',
                    pet_category_snapshot=item.pet.category.name,
                )
                # Reserve the pet
                item.pet.status = 'reserved'
                item.pet.save()
            
            # Create mock payment record
            MockPayment.objects.create(
                order=order,
                amount=total_amount,
            )
            
            orders_created.append(order)
        
        # Clear cart
        cart.clear()
        
        return Response({
            'message': 'Order(s) created successfully.',
            'orders': [OrderListSerializer(o).data for o in orders_created]
        }, status=201)


class OrderListAPIView(APIView):
    """List user's orders."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailAPIView(APIView):
    """Get order details."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        
        # Check permission
        if order.buyer != request.user and order.seller.user != request.user:
            if not request.user.is_superuser and request.user.role != 'admin':
                return Response({'error': 'Permission denied.'}, status=403)
        
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)


class OrderCancelAPIView(APIView):
    """Cancel an order."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
        
        if order.status not in ['pending', 'confirmed']:
            return Response({
                'error': 'This order cannot be cancelled.'
            }, status=400)
        
        order.status = 'cancelled'
        order.save()
        
        # Make pets available again
        for item in order.items.all():
            item.pet.status = 'available'
            item.pet.save()
        
        return Response({'message': 'Order cancelled successfully.'})


class SellerOrderListAPIView(APIView):
    """List orders for seller."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response({'error': 'Seller profile not found.'}, status=404)
        
        orders = Order.objects.filter(
            seller=request.user.seller_profile
        ).order_by('-created_at')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


class SellerOrderUpdateAPIView(APIView):
    """Update order status (seller)."""
    
    permission_classes = [IsAuthenticated, IsSeller]
    
    def patch(self, request, order_number):
        if not hasattr(request.user, 'seller_profile'):
            return Response({'error': 'Seller profile not found.'}, status=404)
        
        order = get_object_or_404(
            Order,
            order_number=order_number,
            seller=request.user.seller_profile
        )
        
        new_status = request.data.get('status')
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped'],
            'shipped': ['delivered'],
        }
        
        if order.status not in valid_transitions:
            return Response({'error': 'Order status cannot be changed.'}, status=400)
        
        if new_status not in valid_transitions.get(order.status, []):
            return Response({
                'error': f'Invalid status transition from {order.status} to {new_status}.'
            }, status=400)
        
        order.status = new_status
        order.save()
        
        # Update pet status when delivered
        if new_status == 'delivered':
            for item in order.items.all():
                item.pet.status = 'sold'
                item.pet.save()
        
        return Response({
            'message': 'Order status updated.',
            'order': OrderDetailSerializer(order).data
        })


# ============ Payment API Views ============

class MockPaymentInitAPIView(APIView):
    """Initialize mock payment."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = get_object_or_404(
            Order,
            order_number=serializer.validated_data['order_number'],
            buyer=request.user
        )
        
        if order.payment_status == 'paid':
            return Response({'error': 'Order is already paid.'}, status=400)
        
        payment = get_object_or_404(MockPayment, order=order)
        payment.status = 'processing'
        payment.save()
        
        return Response({
            'message': 'Payment initiated.',
            'payment': MockPaymentSerializer(payment).data,
            'mock_payment_url': f'/payment/{order.order_number}/'
        })


class MockPaymentCallbackAPIView(APIView):
    """Handle mock payment callback."""
    
    permission_classes = [AllowAny]  # Simulates external webhook
    
    def post(self, request):
        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        order = get_object_or_404(Order, order_number=data['order_number'])
        payment = get_object_or_404(MockPayment, order=order)
        
        if data['status'] == 'success':
            payment.simulate_success()
            order.status = 'confirmed'
            order.save()
            return Response({'message': 'Payment successful.', 'status': 'success'})
        else:
            payment.simulate_failure()
            # Make pets available again
            for item in order.items.all():
                item.pet.status = 'available'
                item.pet.save()
            return Response({'message': 'Payment failed.', 'status': 'failed'})


class PaymentStatusAPIView(APIView):
    """Get payment status."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        
        if order.buyer != request.user and not request.user.is_superuser:
            return Response({'error': 'Permission denied.'}, status=403)
        
        payment = get_object_or_404(MockPayment, order=order)
        return Response(MockPaymentSerializer(payment).data)


# ============ Template Views ============

class CartView(View):
    """Cart page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'orders/cart.html')


class CheckoutView(View):
    """Checkout page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'orders/checkout.html')


class PaymentView(View):
    """Mock payment page."""
    
    def get(self, request, order_number):
        if not request.user.is_authenticated:
            return redirect('login')
        order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
        return render(request, 'orders/payment.html', {'order': order})


class OrderConfirmationView(View):
    """Order confirmation page."""
    
    def get(self, request, order_number):
        if not request.user.is_authenticated:
            return redirect('login')
        order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
        return render(request, 'orders/order_confirmation.html', {'order': order})


class OrderHistoryView(View):
    """Order history page."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'orders/order_history.html')


class OrderDetailView(View):
    """Order detail page."""
    
    def get(self, request, order_number):
        if not request.user.is_authenticated:
            return redirect('login')
        order = get_object_or_404(Order, order_number=order_number)
        if order.buyer != request.user and not request.user.is_superuser:
            return redirect('order_history')
            
        # Calculate timeline for the progress bar
        timeline_steps = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
        order_timeline = [
            ('pending', 'Order Placed'),
            ('confirmed', 'Confirmed'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered')
        ]
        
        order_step = 0
        if order.status in timeline_steps:
            order_step = timeline_steps.index(order.status)
        elif order.status == 'cancelled':
            order_timeline = [('cancelled', 'Order Cancelled')]
            order_step = 0
        elif order.status == 'refunded':
            order_timeline = [('refunded', 'Order Refunded')]
            order_step = 0

        context = {
            'order': order,
            'order_timeline': order_timeline,
            'order_step': order_step
        }
        return render(request, 'orders/order_detail.html', context)
