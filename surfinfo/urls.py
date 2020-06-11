from django.urls import path

from . import views

urlpatterns = [
    path('congratsbro', views.congratsbro, name='congratsbro'),
    path('', views.index, name='index'),
    path('newspotbro', views.newspotbro, name='newspotbro'),
    path('thanksbro', views.thanksbro, name='thanksbro'),
    path('databootstrap', views.databootstrap, name='databootstrap'),
]
