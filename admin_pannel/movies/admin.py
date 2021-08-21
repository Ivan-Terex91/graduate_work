from django.contrib import admin

from .models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork
from .proxy_models import Movie, Serial


class GenreInline(admin.TabularInline):
    model = GenreFilmWork

    autocomplete_fields = ('genre', )

    extra = 0


class PersonRoleInLine(admin.TabularInline):
    model = PersonFilmWork

    autocomplete_fields = ('person', )

    extra = 0


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'creation_date', 'rating')

    fields = (
        'title', 'description', 'creation_date', 'certificate',
        'file_path', 'rating'
    )

    search_fields = ('title', 'description', 'genres__genre', 'persons__person')

    inlines = [
        GenreInline, PersonRoleInLine
    ]


@admin.register(Serial)
class SerialAdmin(admin.ModelAdmin):
    list_display = ('title', 'creation_date', 'rating')

    fields = (
        'title', 'description', 'creation_date', 'certificate',
        'file_path', 'rating'
    )

    search_fields = ('title', 'description', 'id', 'genres__genre', 'persons__person')

    inlines = [
        GenreInline, PersonRoleInLine
    ]


class GenreFilmWorksInLine(admin.TabularInline):
    model = GenreFilmWork

    autocomplete_fields = ('film_work',)

    extra = 0


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)

    fields = (
        'name', 'description'
    )

    inlines = [
        GenreFilmWorksInLine,
    ]

    search_fields = ('name', 'description', 'genres__film_work')


class PersonFilmWorksInLine(admin.TabularInline):
    model = PersonFilmWork

    autocomplete_fields = ('film_work',)

    extra = 0


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_date')

    fields = (
        'name', 'birth_date'
    )

    list_filter = ('persons__role',)

    search_fields = ('name', 'persons__role', 'persons__film_work')

    inlines = [
        PersonFilmWorksInLine,
    ]


# Only for autocomplete_fields of PersonFilmWorksInLine
@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'creation_date', 'rating')

    fields = (
        'title', 'description', 'creation_date', 'certificate',
        'file_path', 'rating', 'type'
    )

    search_fields = ('title', 'description', 'genres__genre', 'persons__person')

    inlines = [
        GenreInline, PersonRoleInLine
    ]
