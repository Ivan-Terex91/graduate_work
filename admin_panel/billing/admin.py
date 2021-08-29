from django.contrib import admin

# from .models import (Order, PaymentMethod, Subscription, SubscriptionMovie,
#                      UsersSubscription)
from .models import (Order, Subscription, SubscriptionMovie,
                     UsersSubscription)


class SubscriptionMovieInLine(admin.TabularInline):
    """Кинопроизведения в подписке"""

    model = SubscriptionMovie
    extra = 0
    verbose_name = "Кинопроизведение в подписке"
    verbose_name_plural = "Кинопроизведения в подписке"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Подписки"""

    list_display = ("id", "title", "period", "type", "price", "currency")
    search_fields = ("title", "period", "type")
    list_filter = ("period", "type")
    inlines = [SubscriptionMovieInLine]
    readonly_fields = ("created", "modified")


@admin.register(UsersSubscription)
class UsersSubscriptionAdmin(admin.ModelAdmin):
    """Подписки клиентов"""

    list_display = ("id", "user_id", "subscription", "status")
    search_fields = ("user_id", "subscription", "status")
    readonly_fields = ("created", "modified")
#
# @admin.register(PaymentMethod)
# class PaymentMethodAdmin(admin.ModelAdmin):
#     """Способы оплаты"""
#
#     list_display = ("id", "payment_system", "type")
#     list_filter = ("payment_system", "type")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Заказы"""

    list_display = ("id", "user_id", "subscription", "status", "total_cost", "currency")
    search_fields = ("user_id", "subscription")
    list_filter = ("status",)
    readonly_fields = ("created", "modified")
