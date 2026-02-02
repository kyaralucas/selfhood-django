from django.urls import path
from . import views 

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("register/thanks/", views.register_thanks, name="register_thanks"),
    path("rest/", views.rest, name="rest"),
]

