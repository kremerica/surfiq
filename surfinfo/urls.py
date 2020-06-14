from django.urls import path

from . import views

urlpatterns = [
    path('congratsbro', views.sessionthankyou, name='congratsbro'),
    path('', views.index, name='index'),
    path('newspotbro', views.requestnewspot, name='newspotbro'),
    path('thanksbro', views.spotthankyou, name='thanksbro'),
    path('databootstrap', views.databootstrap, name='databootstrap'),
    path('wheretobro', views.historicalmatches, name='whereto'),
]
