from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('congratsbro', views.sessionthankyou, name='congratsbro'),
    path('newspotbro', views.requestnewspot, name='newspotbro'),
    path('thanksbro', views.spotthankyou, name='thanksbro'),
    path('wheretobro', views.session_matches_conditions, name='whereto'),
    path('wherewhenbro', views.session_matches_time_and_place, name='wherewhenbro'),
    path('databootstrap', views.databootstrap, name='databootstrap'),
]
