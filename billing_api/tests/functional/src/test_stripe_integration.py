import pytest

from billing_api.models.api_models import PaymentMethodData


@pytest.mark.asyncio
class TestStripe:
    async def test_create_payment_method(
        self, test_stripe_client, test_payment_method_data
    ):
        """Тест метода создания платёжного метода"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        assert payment_method.id
        assert payment_method.type.value == test_payment_method_data["type"]

    async def test_create_customer(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания покупателя"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        customer = await test_stripe_client.create_customer(
            user_id=test_user_data["user_id"],
            user_email=test_user_data["user_email"],
            payment_method=payment_method.id,
        )
        assert customer.id == test_user_data["user_id"]
        assert customer.email == test_user_data["user_email"]

    async def test_create_payment(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания платежа"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        customer = await test_stripe_client.create_customer(
            user_id=test_user_data["user_id"],
            user_email=test_user_data["user_email"],
            payment_method=payment_method.id,
        )

        payment_data = {
            "customer_id": customer.id,
            "amount": 1000,
            "currency": "usd",
            "user_email": customer.email,
            "payment_method_id": payment_method.id,
        }

        payment = await test_stripe_client.create_payment(**payment_data)
        assert payment.id
        assert payment.amount == payment_data["amount"]
        assert payment.status == "requires_confirmation"

    async def test_create_recurrent_payment(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания рекуррентного платежа"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        customer = await test_stripe_client.create_customer(
            user_id=test_user_data["user_id"],
            user_email=test_user_data["user_email"],
            payment_method=payment_method.id,
        )

        payment_data = {
            "customer_id": customer.id,
            "amount": 10000,
            "currency": "usd",
            "user_email": customer.email,
            "payment_method_id": payment_method.id,
        }

        recurrent_payment = await test_stripe_client.create_recurrent_payment(
            **payment_data
        )
        assert recurrent_payment.id
        assert recurrent_payment.amount == payment_data["amount"]
        assert recurrent_payment.status == "succeeded"

    async def test_confirm_payment(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода подтверждения платежа"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        customer = await test_stripe_client.create_customer(
            user_id=test_user_data["user_id"],
            user_email=test_user_data["user_email"],
            payment_method=payment_method.id,
        )

        payment_data = {
            "customer_id": customer.id,
            "amount": 100000,
            "currency": "usd",
            "user_email": customer.email,
            "payment_method_id": payment_method.id,
        }

        payment = await test_stripe_client.create_payment(**payment_data)

        payment_confirm = await test_stripe_client.confirm_payment(
            payment_id=payment.id, payment_method=payment_method.id
        )
        assert payment_confirm.get("id") == payment.id
        assert payment_confirm.get("status") == "succeeded"

    async def test_create_refund(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания возврата"""
        payment_method = await test_stripe_client.create_payment_method(
            payment_method_data=PaymentMethodData(**test_payment_method_data)
        )
        customer = await test_stripe_client.create_customer(
            user_id=test_user_data["user_id"],
            user_email=test_user_data["user_email"],
            payment_method=payment_method.id,
        )

        payment_data = {
            "customer_id": customer.id,
            "amount": 1000000,
            "currency": "usd",
            "user_email": customer.email,
            "payment_method_id": payment_method.id,
        }

        payment = await test_stripe_client.create_payment(**payment_data)

        await test_stripe_client.confirm_payment(
            payment_id=payment.id, payment_method=payment_method.id
        )

        refund = await test_stripe_client.create_refund(
            payment_intent_id=payment.id, amount=payment.amount
        )
        assert refund.id
        assert refund.amount == payment.amount
        assert refund.status == "succeeded"
