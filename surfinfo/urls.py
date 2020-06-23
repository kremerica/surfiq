from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('addsessionbro', views.add_session, name='addsessionbro'),
    path('congratsbro', views.session_thankyou, name='congratsbro'),
    path('newspotbro', views.request_new_spot, name='newspotbro'),
    path('thanksbro', views.spot_thankyou, name='thanksbro'),
    path('wheretobro', views.session_matches_conditions, name='whereto'),
    path('wherewhenbro', views.session_matches_time_and_place, name='wherewhenbro'),
    path('data_bootstrap', views.data_bootstrap, name='data_bootstrap'),
]
