from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # ===== Admin Login =====
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),

    # ===== Dashboard =====
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('api/stats/', views.DashboardStatsAPIView.as_view(), name='api_stats'),

    # ===== User Management =====
    path('users/', views.AdminUsersView.as_view(), name='users'),
    path('api/users/', views.AdminUsersAPIView.as_view(), name='api_users'),
    path('api/users/<int:pk>/', views.AdminUserDetailAPIView.as_view(), name='api_user_detail'),

    # ===== Seller Management =====
    path('sellers/', views.AdminSellersView.as_view(), name='sellers'),
    path('api/sellers/', views.AdminSellersAPIView.as_view(), name='api_sellers'),
    path('api/sellers/<int:pk>/verify/', views.AdminSellerVerifyAPIView.as_view(), name='api_seller_verify'),

    # ===== Pet Management (List + CRUD Forms) =====
    path('pets/', views.AdminPetsView.as_view(), name='pets'),
    path('pets/add/', views.AdminPetAddView.as_view(), name='pet_add'),
    path('pets/<int:pk>/edit/', views.AdminPetEditView.as_view(), name='pet_edit'),

    # ===== Pet API =====
    path('api/pets/', views.AdminPetsAPIView.as_view(), name='api_pets'),
    path('api/pets/create/', views.AdminPetCreateAPIView.as_view(), name='api_pet_create'),
    path('api/pets/<int:pk>/approve/', views.AdminPetApproveAPIView.as_view(), name='api_pet_approve'),
    path('api/pets/<int:pk>/feature/', views.AdminPetFeatureAPIView.as_view(), name='api_pet_feature'),
    path('api/pets/<int:pk>/detail/', views.AdminPetDetailAPIView.as_view(), name='api_pet_detail'),

    # ===== Category & Breed APIs (for CRUD forms) =====
    path('api/categories/', views.AdminCategoriesAPIView.as_view(), name='api_categories'),
    path('api/breeds/', views.AdminBreedsAPIView.as_view(), name='api_breeds'),

    # ===== Order Management =====
    path('orders/', views.AdminOrdersView.as_view(), name='orders'),
    path('api/orders/', views.AdminOrdersAPIView.as_view(), name='api_orders'),

    # ===== Adoption Management =====
    path('adoptions/', views.AdminAdoptionsView.as_view(), name='adoptions'),
    path('api/adoptions/', views.AdminAdoptionsAPIView.as_view(), name='api_adoptions'),

    # ===== Review Management =====
    path('reviews/', views.AdminReviewsView.as_view(), name='reviews'),
    path('api/reviews/', views.AdminReviewsAPIView.as_view(), name='api_reviews'),

    # ===== Analytics =====
    path('analytics/', views.AdminAnalyticsView.as_view(), name='analytics'),
    path('api/analytics/', views.AdminAnalyticsAPIView.as_view(), name='api_analytics'),
]
