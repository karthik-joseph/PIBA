from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints
    path('api/v1/sellers/', views.SellerListAPIView.as_view(), name='api_seller_list'),
    path('api/v1/sellers/profile/', views.SellerProfileAPIView.as_view(), name='api_seller_profile'),
    path('api/v1/sellers/dashboard/stats/', views.SellerDashboardStatsAPIView.as_view(), name='api_seller_stats'),
    path('api/v1/sellers/documents/upload/', views.SellerDocumentUploadAPIView.as_view(), name='api_seller_document_upload'),
    path('api/v1/sellers/<int:pk>/', views.SellerDetailAPIView.as_view(), name='api_seller_detail'),
    path('api/v1/sellers/<int:pk>/verify/', views.SellerVerifyAPIView.as_view(), name='api_seller_verify'),

    # Template Views
    path('seller/dashboard/', views.SellerDashboardView.as_view(), name='seller_dashboard'),
    path('seller/pets/', views.SellerManagePetsView.as_view(), name='seller_manage_pets'),
    path('seller/pets/add/', views.SellerAddPetView.as_view(), name='seller_add_pet'),
    path('seller/pets/<slug:slug>/edit/', views.SellerEditPetView.as_view(), name='seller_edit_pet'),
    path('seller/orders/', views.SellerOrdersView.as_view(), name='seller_orders'),
    path('sellers/<int:pk>/', views.SellerPublicProfileView.as_view(), name='seller_public_profile'),
]
