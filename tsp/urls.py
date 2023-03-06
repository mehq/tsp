from django.urls import include, path

urlpatterns = [
    path("", include("tsp.apps.core.urls")),
]
