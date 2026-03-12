from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import User
from users.permissions import IsAdmin
from pets.models import Pet, PetCategory, Breed
from sellers.models import SellerProfile
from orders.models import Order
from adoption.models import AdoptionRequest
from reviews.models import PetReview, SellerReview


def admin_required(view_func):
    """Decorator to check admin access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('custom_admin:admin_login')
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


class AdminRequiredMixin:
    """Mixin for admin-only views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('custom_admin:admin_login')
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('custom_admin:admin_login')
        return super().dispatch(request, *args, **kwargs)


# ============ Admin Login ============

class AdminLoginView(View):
    """Separate login page for admin access."""

    def get(self, request):
        if request.user.is_authenticated and (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('custom_admin:dashboard')
        return render(request, 'custom_admin/admin_login.html')



# ============ Dashboard ============

class DashboardView(AdminRequiredMixin, View):
    """Admin dashboard home."""
    
    def get(self, request):
        return render(request, 'custom_admin/dashboard.html')


class DashboardStatsAPIView(APIView):
    """API endpoint for dashboard statistics."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        stats = {
            'users': {
                'total': User.objects.count(),
                'new_this_week': User.objects.filter(date_joined__gte=week_ago).count(),
                'buyers': User.objects.filter(role='buyer').count(),
                'sellers': User.objects.filter(role='seller').count(),
            },
            'pets': {
                'total': Pet.objects.count(),
                'available': Pet.objects.filter(status='available', is_approved=True).count(),
                'pending_approval': Pet.objects.filter(is_approved=False, is_active=True).count(),
                'sold': Pet.objects.filter(status='sold').count(),
                'adopted': Pet.objects.filter(status='adopted').count(),
            },
            'sellers': {
                'total': SellerProfile.objects.count(),
                'verified': SellerProfile.objects.filter(is_verified=True).count(),
                'pending_verification': SellerProfile.objects.filter(is_verified=False).count(),
            },
            'orders': {
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status='pending').count(),
                'delivered': Order.objects.filter(status='delivered').count(),
                'revenue': float(Order.objects.filter(
                    status='delivered', payment_status='paid'
                ).aggregate(total=Sum('total_amount'))['total'] or 0),
            },
            'adoptions': {
                'total': AdoptionRequest.objects.count(),
                'pending': AdoptionRequest.objects.filter(status='pending').count(),
                'approved': AdoptionRequest.objects.filter(status='approved').count(),
            },
            'recent_orders': list(Order.objects.order_by('-created_at')[:5].values(
                'order_number', 'status', 'total_amount', 'created_at'
            )),
        }
        
        return Response(stats)


# ============ User Management ============

class AdminUsersView(AdminRequiredMixin, View):
    """User management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/users.html')


class AdminUsersAPIView(APIView):
    """API endpoint for user management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        role = request.query_params.get('role')
        search = request.query_params.get('search')
        
        users = User.objects.all().order_by('-date_joined')
        
        if role:
            users = users.filter(role=role)
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search)
            )
        
        data = list(users[:100].values(
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'is_active', 'is_verified', 'date_joined'
        ))
        return Response(data)


class AdminUserDetailAPIView(APIView):
    """API endpoint for user detail/actions."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined,
        })
    
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
        if 'is_verified' in request.data:
            user.is_verified = request.data['is_verified']
        if 'role' in request.data:
            user.role = request.data['role']
        
        user.save()
        return Response({'message': 'User updated successfully.'})


# ============ Seller Management ============

class AdminSellersView(AdminRequiredMixin, View):
    """Seller management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/sellers.html')


class AdminSellersAPIView(APIView):
    """API endpoint for seller management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        verified = request.query_params.get('verified')
        
        sellers = SellerProfile.objects.all().order_by('-joined_at')
        
        if verified is not None:
            sellers = sellers.filter(is_verified=verified.lower() == 'true')
        
        data = list(sellers[:100].values(
            'id', 'business_name', 'business_type', 'city', 'state',
            'is_verified', 'rating', 'total_sales', 'joined_at'
        ))
        return Response(data)


class AdminSellerVerifyAPIView(APIView):
    """API endpoint for seller verification."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        seller = get_object_or_404(SellerProfile, pk=pk)
        action = request.data.get('action')
        
        if action == 'verify':
            seller.is_verified = True
            seller.verification_date = timezone.now()
            seller.save()
            return Response({'message': 'Seller verified successfully.'})
        elif action == 'unverify':
            seller.is_verified = False
            seller.save()
            return Response({'message': 'Seller unverified.'})
        
        return Response({'error': 'Invalid action.'}, status=400)


# ============ Pet Management ============

class AdminPetsView(AdminRequiredMixin, View):
    """Pet management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/pets.html')


class AdminPetsAPIView(APIView):
    """API endpoint for pet management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        approved = request.query_params.get('approved')
        status_filter = request.query_params.get('status')
        
        pets = Pet.objects.all().order_by('-created_at')
        
        if approved is not None:
            pets = pets.filter(is_approved=approved.lower() == 'true')
        if status_filter:
            pets = pets.filter(status=status_filter)
        
        data = []
        for pet in pets[:100]:
            data.append({
                'id': pet.id,
                'name': pet.name,
                'slug': pet.slug,
                'category': pet.category.name,
                'seller': pet.seller.business_name,
                'price': float(pet.price),
                'status': pet.status,
                'is_approved': pet.is_approved,
                'is_featured': pet.is_featured,
                'created_at': pet.created_at,
            })
        return Response(data)


class AdminPetApproveAPIView(APIView):
    """API endpoint for pet approval."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        action = request.data.get('action')
        
        if action == 'approve':
            pet.is_approved = True
            pet.save()
            return Response({'message': 'Pet approved successfully.'})
        elif action == 'reject':
            pet.is_approved = False
            pet.save()
            return Response({'message': 'Pet rejected.'})
        
        return Response({'error': 'Invalid action.'}, status=400)


class AdminPetFeatureAPIView(APIView):
    """API endpoint for pet featuring."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        pet.is_featured = not pet.is_featured
        pet.save()
        return Response({
            'message': f'Pet {"featured" if pet.is_featured else "unfeatured"}.',
            'is_featured': pet.is_featured
        })


class AdminPetDetailAPIView(APIView):
    """API endpoint for pet detail read/update/delete (admin CRUD)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        data = {
            'id': pet.id,
            'name': pet.name,
            'slug': pet.slug,
            'category': pet.category_id,
            'category_name': pet.category.name,
            'breed': pet.breed_id,
            'breed_name': pet.breed.name if pet.breed else None,
            'seller': pet.seller_id,
            'seller_name': pet.seller.business_name,
            'price': float(pet.price),
            'listing_type': pet.listing_type,
            'status': pet.status,
            'gender': pet.gender,
            'age_years': pet.age_years,
            'age_months': pet.age_months,
            'color': pet.color,
            'weight': float(pet.weight) if pet.weight else None,
            'description': pet.description,
            'health_status': pet.health_status,
            'is_vaccinated': pet.is_vaccinated,
            'is_neutered': pet.is_neutered,
            'is_approved': pet.is_approved,
            'is_featured': pet.is_featured,
            'is_active': pet.is_active,
            'primary_image_url': pet.primary_image_url,
            'created_at': pet.created_at,
        }
        return Response(data)

    def patch(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        data = request.data

        fields = [
            'name', 'price', 'listing_type', 'status', 'gender',
            'age_years', 'age_months', 'color', 'weight', 'description',
            'health_status', 'is_vaccinated', 'is_neutered',
            'is_approved', 'is_featured', 'is_active',
        ]
        for field in fields:
            if field in data:
                setattr(pet, field, data[field])

        if 'category' in data:
            pet.category = get_object_or_404(PetCategory, pk=data['category'])
        if 'breed' in data:
            if data['breed']:
                try:
                    pet.breed = Breed.objects.get(pk=data['breed'])
                except Breed.DoesNotExist:
                    pet.breed = None
            else:
                pet.breed = None
        if 'seller' in data:
            pet.seller = get_object_or_404(SellerProfile, pk=data['seller'])

        pet.save()
        return Response({'message': 'Pet updated successfully.'})

    def delete(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        pet.delete()
        return Response({'message': 'Pet deleted.'}, status=204)


class AdminPetCreateAPIView(APIView):
    """API endpoint to create a new pet (admin CRUD)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        data = request.data
        required = ['name', 'category', 'seller', 'price']
        for field in required:
            if not data.get(field):
                return Response({'error': f'{field} is required.'}, status=400)

        try:
            category = PetCategory.objects.get(pk=data['category'])
            seller = SellerProfile.objects.get(pk=data['seller'])
        except (PetCategory.DoesNotExist, SellerProfile.DoesNotExist) as e:
            return Response({'error': str(e)}, status=400)

        breed = None
        if data.get('breed'):
            try:
                breed = Breed.objects.get(pk=data['breed'])
            except Breed.DoesNotExist:
                pass

        pet = Pet(
            name=data['name'],
            category=category,
            seller=seller,
            breed=breed,
            price=data['price'],
            listing_type=data.get('listing_type', 'sale'),
            status=data.get('status', 'available'),
            gender=data.get('gender', 'unknown'),
            age_years=data.get('age_years', 0),
            age_months=data.get('age_months', 0),
            color=data.get('color', ''),
            weight=data.get('weight') or None,
            description=data.get('description', ''),
            health_status=data.get('health_status', 'good'),
            is_vaccinated=data.get('is_vaccinated', False),
            is_neutered=data.get('is_neutered', False),
            is_approved=data.get('is_approved', False),
            is_featured=data.get('is_featured', False),
            is_active=data.get('is_active', True),
        )
        pet.save()
        return Response({'message': 'Pet created.', 'id': pet.id}, status=201)


# ============ Category and Breed APIs ============

class AdminCategoriesAPIView(APIView):
    """API to list all pet categories (for forms)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        cats = list(PetCategory.objects.filter(is_active=True).values('id', 'name', 'slug'))
        return Response(cats)


class AdminBreedsAPIView(APIView):
    """API to list breeds, optionally filtered by category."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        category_id = request.query_params.get('category')
        breeds = Breed.objects.filter(is_active=True)
        if category_id:
            breeds = breeds.filter(category_id=category_id)
        data = list(breeds.values('id', 'name', 'category_id'))
        return Response(data)


# ============ Pet CRUD Template Views ============

class AdminPetAddView(AdminRequiredMixin, View):
    """Template view to add a new pet."""

    def get(self, request):
        return render(request, 'custom_admin/pet_form.html', {'pet': None})


class AdminPetEditView(AdminRequiredMixin, View):
    """Template view to edit an existing pet."""

    def get(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        return render(request, 'custom_admin/pet_form.html', {'pet': pet})



# ============ Order Management ============

class AdminOrdersView(AdminRequiredMixin, View):
    """Order management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/orders.html')


class AdminOrdersAPIView(APIView):
    """API endpoint for order management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        status_filter = request.query_params.get('status')
        
        orders = Order.objects.all().order_by('-created_at')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        data = []
        for order in orders[:100]:
            data.append({
                'order_number': order.order_number,
                'buyer': order.buyer.email,
                'seller': order.seller.business_name,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at,
            })
        return Response(data)


# ============ Adoption Management ============

class AdminAdoptionsView(AdminRequiredMixin, View):
    """Adoption management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/adoptions.html')


class AdminAdoptionsAPIView(APIView):
    """API endpoint for adoption management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        status_filter = request.query_params.get('status')
        
        requests = AdoptionRequest.objects.all().order_by('-submitted_at')
        
        if status_filter:
            requests = requests.filter(status=status_filter)
        
        data = []
        for req in requests[:100]:
            data.append({
                'id': req.id,
                'pet_name': req.pet.name,
                'applicant': req.applicant.email,
                'status': req.status,
                'submitted_at': req.submitted_at,
            })
        return Response(data)


# ============ Review Management ============

class AdminReviewsView(AdminRequiredMixin, View):
    """Review management page."""
    
    def get(self, request):
        return render(request, 'custom_admin/reviews.html')


class AdminReviewsAPIView(APIView):
    """API endpoint for review management."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        review_type = request.query_params.get('type', 'pet')
        approved = request.query_params.get('approved')
        
        if review_type == 'seller':
            reviews = SellerReview.objects.all().order_by('-created_at')
        else:
            reviews = PetReview.objects.all().order_by('-created_at')
        
        if approved is not None:
            reviews = reviews.filter(is_approved=approved.lower() == 'true')
        
        data = []
        for review in reviews[:100]:
            item = {
                'id': review.id,
                'reviewer': review.reviewer.email,
                'rating': review.rating,
                'title': review.title,
                'is_approved': review.is_approved,
                'created_at': review.created_at,
            }
            if review_type == 'seller':
                item['seller'] = review.seller.business_name
            else:
                item['pet'] = review.pet.name
            data.append(item)
        
        return Response(data)


# ============ Analytics ============

class AdminAnalyticsView(AdminRequiredMixin, View):
    """Analytics page."""
    
    def get(self, request):
        return render(request, 'custom_admin/analytics.html')


class AdminAnalyticsAPIView(APIView):
    """API endpoint for analytics data."""
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        # Orders over time (last 30 days)
        now = timezone.now()
        orders_by_day = []
        for i in range(30):
            day = now - timedelta(days=29-i)
            count = Order.objects.filter(
                created_at__date=day.date()
            ).count()
            revenue = Order.objects.filter(
                created_at__date=day.date(),
                payment_status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            orders_by_day.append({
                'date': day.strftime('%Y-%m-%d'),
                'orders': count,
                'revenue': float(revenue)
            })
        
        # Pets by category
        pets_by_category = list(
            Pet.objects.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Users by role
        users_by_role = list(
            User.objects.values('role')
            .annotate(count=Count('id'))
        )
        
        # Top sellers
        top_sellers = list(
            SellerProfile.objects.filter(is_verified=True)
            .order_by('-total_sales')[:10]
            .values('business_name', 'total_sales', 'rating')
        )
        
        return Response({
            'orders_by_day': orders_by_day,
            'pets_by_category': pets_by_category,
            'users_by_role': users_by_role,
            'top_sellers': top_sellers,
        })
