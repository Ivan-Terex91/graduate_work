from django.contrib.postgres.aggregates import ArrayAgg
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import Movie


class MoviesApiMixin:
    """Вспомогательный класс миксин"""
    model = Movie
    http_method_names = ['get']
    queryset = Movie.objects.prefetch_related('genres', 'persons').annotate(
        rol=ArrayAgg('movieperson__role', ordering='persons')).annotate(
        gen=ArrayAgg('genres__name', distinct=True)).order_by('creation_date')

    @staticmethod
    def get_serialize_object(obj):
        """Формируем фильм с полями которые нужны для выдачи"""

        genres = obj.gen
        roles = obj.rol
        actors, writers, directors = [], [], []
        persons = [' '.join((person.firstname, person.lastname)).strip() for person in obj.persons.all()]
        persons_role = list(zip(persons, roles))

        for person in persons_role:
            if person[1] == 'actor':
                actors.append(person[0])
            elif person[1] == 'writer':
                writers.append(person[0])
            elif person[1] == 'director':
                directors.append(person[0])

        movie = {
            'id': obj.id, 'title': obj.title, 'description': obj.description,
            'creation_date': obj.creation_date, 'rating': obj.rating,
            'type': obj.movie_type,
            'genres': genres,
            'actors': actors, 'directors': directors, 'writers': writers,
        }
        return movie

    def render_to_response(self, context):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    """Вывод списка кинопроизведений"""
    model = Movie
    http_method_names = ['get']
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        genre = self.request.GET.get('genre', '')
        title = self.request.GET.get('title', '')
        self.queryset = self.queryset.filter(gen__icontains=genre, title__icontains=title)

        paginator, page, query, is_paginated = self.paginate_queryset(self.queryset, self.paginate_by)
        results = []

        for obj in query:
            movie = self.get_serialize_object(obj)
            results.append(movie)

        context = {
            'count': self.queryset.count(),
            "total_pages": paginator.num_pages,
            "prev": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            'results': results,
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    """Вывод одного кинопроизведения"""

    def get_context_data(self, **kwargs):
        movie = self.queryset.get(pk=self.kwargs.get('pk'))
        movie = self.get_serialize_object(movie)

        return movie
