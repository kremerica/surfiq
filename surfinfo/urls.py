from django.urls import path

from . import views

urlpatterns = [
    path('addsession', views.addsession, name='addsession'),
]