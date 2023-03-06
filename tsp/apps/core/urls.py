from django.urls import path

from .views import get_tsp_solution, health_check, solve_tsp

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("api/solve-tsp/", solve_tsp, name="solve-tsp"),
    path("api/solve-tsp/<uuid:problem_id>", get_tsp_solution, name="get-tsp-solution"),
]
