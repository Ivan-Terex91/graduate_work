import math

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import FilmWork


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    def get_queryset(self):
        return (
            self.model.objects.values(
                'id',
                'title',
                'description',
                'creation_date',
                'certificate',
                'rating',
                'type',
            )
            .annotate(genres=ArrayAgg('genres__name', distinct=True))
            .annotate(
                actors=ArrayAgg(
                    'film_works_p__person__name',
                    filter=Q(film_works_p__role='actor'),
                    distinct=True,
                )
            )
            .annotate(
                directors=ArrayAgg(
                    'film_works_p__person__name',
                    filter=Q(film_works_p__role='director'),
                    distinct=True,
                )
            )
            .annotate(
                writers=ArrayAgg(
                    'film_works_p__person__name',
                    filter=Q(film_works_p__role='writer'),
                    distinct=True,
                )
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class Movies(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        page_size = self.get_paginate_by(queryset)
        count_of_queries = queryset.count()

        _, page, queryset, _ = self.paginate_queryset(queryset, page_size)

        context = {
            'count': count_of_queries,
            'total_pages': math.ceil(count_of_queries / page_size),
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            'results': list(queryset),
        }

        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        obj = self.get_object(queryset)

        return obj
