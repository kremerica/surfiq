from django.urls import path

from . import views

urlpatterns = [
    path('congratsbro', views.congratsbro, name='congratsbro'),
    path('', views.index, name='index'),
]
