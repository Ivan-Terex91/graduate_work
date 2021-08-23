from django.contrib import admin

from .models import Movie, Person, Genre


class PersonInline(admin.TabularInline):
    model = Movie.persons.through
    extra = 0
    verbose_name = 'человек учавствовавший в кинопроизведении'
    verbose_name_plural = 'люди учавствовавшие в кинопроизведении'


class MovieInline(admin.TabularInline):
    model = Movie.persons.through
    extra = 0
    verbose_name = 'фильм в котором учавствовал человек'
    verbose_name_plural = 'фильмы в которых учавствовал в человек'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Кинопроизведения."""
    list_display = ('title', 'movie_type', 'creation_date', 'rating', 'imdb_rating', 'age_limit')
    exclude = ('id',)
    inlines = [PersonInline]
    search_fields = ('title',)
    list_filter = ('movie_type', 'age_limit')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """Люди."""
    list_display = ('firstname', 'lastname', 'birthdate', 'birthplace')
    exclude = ('id',)
    search_fields = ('firstname', 'lastname')
    inlines = [MovieInline]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Жанры."""
    list_display = ('name',)
    exclude = ('id',)
