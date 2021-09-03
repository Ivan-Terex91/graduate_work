from models.api_models import PaymentMethodDataOut
from models.db_models import PaymentMethod
from pydantic import UUID4


class PaymentMethodRepository:
    """Класс для работы с таблицей методов оплаты."""

    @staticmethod
    async def create_payment_method(
        payment_method_data: PaymentMethodDataOut, user_id: UUID4
    ):
        """Создание платёжного метода"""
        payment_method = await PaymentMethod.create(
            **payment_method_data.dict(), user_id=user_id
        )
        return payment_method
