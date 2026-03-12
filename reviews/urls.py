from django.urls import path
from . import views

urlpatterns = [
    # Pet Reviews API
    path('api/v1/reviews/pets/<slug:pet_slug>/', views.PetReviewListAPIView.as_view(), name='api_pet_reviews'),
    path('api/v1/reviews/pets/<slug:pet_slug>/create/', views.PetReviewCreateAPIView.as_view(), name='api_pet_review_create'),
    
    # Seller Reviews API
    path('api/v1/reviews/sellers/<int:seller_id>/', views.SellerReviewListAPIView.as_view(), name='api_seller_reviews'),
    path('api/v1/reviews/sellers/<int:seller_id>/create/', views.SellerReviewCreateAPIView.as_view(), name='api_seller_review_create'),
    
    # Review Response & Moderation
    path('api/v1/reviews/<int:pk>/respond/', views.ReviewResponseAPIView.as_view(), name='api_review_respond'),
    path('api/v1/reviews/<int:pk>/moderate/', views.ReviewModerateAPIView.as_view(), name='api_review_moderate'),
    
    # Template Views
    path('reviews/write/<slug:pet_slug>/', views.WriteReviewView.as_view(), name='write_review'),
]
