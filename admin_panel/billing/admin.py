from django.contrib import admin
from .models import Subscription, SubscriptionMovie, Order, Product


class SubscriptionMovieInLine(admin.TabularInline):
    """Кинопроизведения в подписке"""
    model = SubscriptionMovie
    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Подписки"""
    list_display = ('id', 'name', 'period')
    search_fields = ('id', 'name', 'period')

    inlines = [
        SubscriptionMovieInLine
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Продукты"""
    list_display = ('id', 'description', 'price', 'currency')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Заказы"""
    list_display = ('id', 'user_id', 'product', 'status', 'payment_method')
    search_fields = ('user_id', 'product')
    list_filter = ('status',)
