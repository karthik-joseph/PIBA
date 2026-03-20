from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # API Endpoints
    path('api/v1/auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/v1/auth/seller/register/', views.SellerRegisterAPIView.as_view(), name='api_seller_register'),
    path('api/v1/auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/v1/auth/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/v1/auth/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
    path('api/v1/auth/password/change/', views.PasswordChangeAPIView.as_view(), name='api_password_change'),
    path('api/v1/auth/me/', views.UserDetailAPIView.as_view(), name='api_user_detail'),
    path('api/v1/wishlist/', views.WishlistAPIView.as_view(), name='api_wishlist'),
    path('api/v1/wishlist/toggle/<int:pet_id>/', views.WishlistToggleAPIView.as_view(), name='api_wishlist_toggle'),

    # Template Views
    path('register/', views.RegisterView.as_view(), name='register'),
    path('seller/register/', views.SellerRegisterView.as_view(), name='seller_register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('terms-of-use/', views.TermsOfUseView.as_view(), name='terms'),
    path('refund-policy/', views.RefundPolicyView.as_view(), name='refund_policy'),
]

# End of users routing
