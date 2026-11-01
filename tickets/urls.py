from django.urls import path

from tickets import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('tickets/new/', views.TicketCreateView.as_view(), name='create'),
    path('tickets/<int:pk>/edit/', views.TicketUpdateView.as_view(), name='update'),
]
