from django.urls import path

from .views import MoviesDetailApi, MoviesListApi

urlpatterns = [
    path("movies/<uuid:pk>/", MoviesDetailApi.as_view(), name="movie_detail"),
    path("movies/", MoviesListApi.as_view(), name="movie_list"),
]
