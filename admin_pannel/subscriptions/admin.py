from django.contrib import admin

from .models import Subscription, SubscriptionFilm


class SubscriptionFilmInLine(admin.TabularInline):
    model = SubscriptionFilm

    # autocomplete_fields = ('person', )

    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'period')

    search_fields = ('id', 'name', 'period')

    inlines = [
        SubscriptionFilmInLine
    ]