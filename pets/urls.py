from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints
    path('api/v1/pets/', views.PetListAPIView.as_view(), name='api_pet_list'),
    path('api/v1/pets/featured/', views.FeaturedPetsAPIView.as_view(), name='api_featured_pets'),
    path('api/v1/pets/categories/', views.CategoryListAPIView.as_view(), name='api_category_list'),
    path('api/v1/pets/breeds/', views.BreedListAPIView.as_view(), name='api_breed_list'),
    path('api/v1/pets/breeds/<int:category_id>/', views.BreedByCategoryAPIView.as_view(), name='api_breeds_by_category'),
    path('api/v1/pets/states/', views.SellerStatesAPIView.as_view(), name='api_seller_states'),
    path('api/v1/pets/my-listings/', views.MyPetListingsAPIView.as_view(), name='api_my_listings'),
    path('api/v1/pets/create/', views.PetCreateAPIView.as_view(), name='api_pet_create'),
    path('api/v1/pets/<slug:slug>/', views.PetDetailAPIView.as_view(), name='api_pet_detail'),
    path('api/v1/pets/<slug:slug>/update/', views.PetUpdateAPIView.as_view(), name='api_pet_update'),
    path('api/v1/pets/<slug:slug>/images/', views.PetImageUploadAPIView.as_view(), name='api_pet_images'),
    path('api/v1/pets/<slug:slug>/similar/', views.SimilarPetsAPIView.as_view(), name='api_similar_pets'),

    # Template Views
    path('pets/', views.PetListingView.as_view(), name='pet_listing'),
    path('pets/category/<slug:slug>/', views.CategoryPetsView.as_view(), name='category_pets'),
    path('pets/<slug:slug>/', views.PetDetailView.as_view(), name='pet_detail'),
]
