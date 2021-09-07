from unittest import mock

import pytest

from billing_api.models.api_models import PaymentMethodData


@pytest.mark.asyncio
class TestStripe:
    async def test_create_payment_method(
        self, test_stripe_client, test_payment_method_data
    ):
        """Тест метода создания платёжного метода"""
        expected_id = "test_id"
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {"id": expected_id}
            payment_method = await test_stripe_client.create_payment_method(
                payment_method_data=PaymentMethodData(**test_payment_method_data)
            )
        assert payment_method.id == expected_id
        assert payment_method.type.value == test_payment_method_data["type"]

    async def test_create_customer(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания покупателя"""
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {
                "id": test_user_data["user_id"],
                "email": test_user_data["user_email"],
            }
            customer = await test_stripe_client.create_customer(
                user_id=test_user_data["user_id"],
                user_email=test_user_data["user_email"],
            )
        assert customer.id == test_user_data["user_id"]
        assert customer.email == test_user_data["user_email"]

    async def test_create_payment(
        self,
        test_stripe_client,
        test_payment_method_data,
        test_user_data,
        test_payment_data,
    ):
        """Тест метода создания платежа"""
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {
                "id": "expected_id",
                "amount": test_payment_data["amount"],
                "status": "requires_confirmation",
            }
            payment = await test_stripe_client.create_payment(**test_payment_data)
        assert payment.id
        assert payment.amount == test_payment_data["amount"]
        assert payment.status == "requires_confirmation"

    async def test_create_recurrent_payment(
        self,
        test_stripe_client,
        test_payment_method_data,
        test_user_data,
        test_payment_data,
    ):
        """Тест метода создания рекуррентного платежа"""
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {
                "id": "expected_id",
                "amount": test_payment_data["amount"],
                "status": "succeeded",
            }
            recurrent_payment = await test_stripe_client.create_recurrent_payment(
                **test_payment_data
            )
        assert recurrent_payment.id
        assert recurrent_payment.amount == test_payment_data["amount"]
        assert recurrent_payment.status == "succeeded"

    async def test_confirm_payment(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода подтверждения платежа"""
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {"id": "expected_id", "status": "succeeded"}

            payment_confirm = await test_stripe_client.confirm_payment(
                payment_id="payment.id", payment_method="payment_method.id"
            )
        assert payment_confirm.get("id") == "expected_id"
        assert payment_confirm.get("status") == "succeeded"

    async def test_create_refund(
        self, test_stripe_client, test_payment_method_data, test_user_data
    ):
        """Тест метода создания возврата"""
        with mock.patch.object(test_stripe_client, "_request") as mock_request:
            mock_request.return_value = {
                "id": "expected_id",
                "amount": 100000,
                "status": "succeeded",
            }
            refund = await test_stripe_client.create_refund(
                payment_intent_id="payment.id", amount="payment.amount"
            )
        assert refund.id
        assert refund.amount == 100000
        assert refund.status == "succeeded"
