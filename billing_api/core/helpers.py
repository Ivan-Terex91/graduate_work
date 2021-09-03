from datetime import date
from decimal import Decimal
from typing import Optional


def get_refund_amount(
    end_date: date, amount: Decimal, period: int
) -> Optional[Decimal]:
    """Функция рассчёта суммы возврата"""
    today = date.today()
    if end_date < today:
        return None

    remaining_days = end_date - today
    return amount * remaining_days.days / period


def get_amount(price: Decimal):
    """
    Функция пересчёта цены в наименьший денежный эквивалент
    (руб -> коп, usd -> cent)
    """

    return int(price * 100)
