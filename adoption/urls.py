from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints
    path('api/v1/adoption/apply/', views.AdoptionApplyAPIView.as_view(), name='api_adoption_apply'),
    path('api/v1/adoption/my-requests/', views.MyAdoptionRequestsAPIView.as_view(), name='api_my_adoption_requests'),
    path('api/v1/adoption/requests/', views.AdoptionRequestListAPIView.as_view(), name='api_adoption_requests'),
    path('api/v1/adoption/requests/<int:pk>/', views.AdoptionRequestDetailAPIView.as_view(), name='api_adoption_request_detail'),
    path('api/v1/adoption/requests/<int:pk>/update/', views.AdoptionRequestUpdateAPIView.as_view(), name='api_adoption_request_update'),
    path('api/v1/adoption/follow-ups/', views.AdoptionFollowUpAPIView.as_view(), name='api_adoption_followups'),

    # Template Views
    path('adoption/apply/<slug:pet_slug>/', views.AdoptionApplyView.as_view(), name='adoption_apply'),
    path('adoption/my-requests/', views.MyAdoptionRequestsView.as_view(), name='my_adoption_requests'),
    path('adoption/requests/<int:pk>/', views.AdoptionRequestDetailView.as_view(), name='adoption_request_detail'),
]
