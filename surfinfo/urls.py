from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('addsessionbro', views.add_session, name='add_session'),
    path('congratsbro', views.session_thankyou, name='session_thankyou'),
    path('newspotbro', views.request_new_spot, name='request_new_spot'),
    path('thanksbro', views.spot_thankyou, name='spot_thankyou'),
    path('wheretobro', views.session_matches_conditions, name='session_matches_conditions'),
    path('wherewhenbro', views.session_matches_time_and_place, name='session_matches_time_and_place'),
    path('data_bootstrap', views.data_bootstrap, name='data_bootstrap'),
]
