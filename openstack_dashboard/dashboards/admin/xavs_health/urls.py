from django.urls import re_path
from . import views

app_name = "xavs_health"

urlpatterns = [
    re_path(r"^$", views.IndexView.as_view(), name="index"),
]
