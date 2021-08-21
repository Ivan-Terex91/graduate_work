from django.contrib import admin

from .models import Sub, Sub_film_work, Order


class SubscriptionFilmInLine(admin.TabularInline):
    model = Sub_film_work

    extra = 0


@admin.register(Sub)
class SubAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'price')

    search_fields = ('id', 'name', 'period', 'price')

    inlines = [
        SubscriptionFilmInLine
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'sub', 'type')

    search_fields = ('user_id', 'sub')