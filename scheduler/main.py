import logging
import time
from datetime import date

import backoff
import schedule
from requests import request  # type: ignore
from requests.exceptions import RequestException  # type: ignore

from settings import Settings  # type: ignore

settings = Settings()
logger = logging.getLogger("scheduler")


class SchedulerService:
    """Класс для работы планировщика"""

    def __init__(self, billing_settings: Settings):
        self.billing_api_url = billing_settings.BILLING_API_URL
        self.base_endpoint = billing_settings.BILLING_API_BASE_ENDPOINT

    @backoff.on_exception(
        exception=RequestException, wait_gen=backoff.expo, max_time=30, logger=logger
    )
    def _request(
        self, method: str, endpoint: str, headers: dict = None, data: dict = None
    ):
        response = request(
            method=method,
            url=f"{self.billing_api_url}{self.base_endpoint}{endpoint}",
            headers=headers,
            json=data,
        )
        if response.ok:
            return response.json()
        logger.exception(
            "Error when requesting the billing api status_code=%s,  reason - %s",
            response.status_code,
            response.reason,
        )

    def check_processing_orders(self) -> None:
        """Метод проверки оплаты заказов в обработке"""
        try:
            processing_orders = self._request(
                method="GET", endpoint="/orders/processing"
            )
            logger.info("%s orders in processing", len(processing_orders))
            for order in processing_orders:
                self.check_order_payment(order_external_id=order.get("external_id"))
                time.sleep(1)
        except Exception as e:
            logger.exception("Error when trying to check processing orders: %s", e)

    def check_order_payment(self, order_external_id: str) -> None:
        """Метод проверки оплаты заказа"""
        try:
            self._request(method="GET", endpoint=f"/order/{order_external_id}/check")
        except Exception as e:
            logger.exception(
                "Error when trying to check payment for order %s: %s",
                order_external_id,
                e,
            )

    def check_processing_refunds(self) -> None:
        """Метод проверки проведения возвратов в обработке"""
        try:
            processing_refunds_orders = self._request(
                method="GET", endpoint="/refunds/processing"
            )
            logger.info("%s refunds in processing", len(processing_refunds_orders))
            for refund_order in processing_refunds_orders:
                self.check_refund_execution(
                    refund_external_id=refund_order.get("external_id")
                )
                time.sleep(1)
        except Exception as e:
            logger.exception("Error when trying to check processing refunds: %s", e)

    def check_refund_execution(self, refund_external_id: str) -> None:
        """Метод проверки выполнения возврата"""
        try:
            self._request(method="GET", endpoint=f"/refund/{refund_external_id}/check")
        except Exception as e:
            logger.exception(
                "Error when trying to check refund execution %s: %s",
                refund_external_id,
                e,
            )

    def disable_expired_user_subscription(self) -> None:
        """Метод отключает все истёкшие подписки пользователя"""
        try:
            self._request(method="GET", endpoint="/subscriptions/expired/disable")
            logger.info("Expired subscriptions on %s are disabled", date.today())
        except Exception as e:
            logger.exception(
                "Error when trying to disable expired user subscriptions : %s", e
            )

    def check_expiring_active_subscriptions_automatic(self):
        """Метод проверки всех активных подписок пользователей, срок действия которых истекает завтра"""
        try:
            expiring_subscriptions = self._request(
                method="GET", endpoint="/subscriptions/automatic/active"
            )
            logger.info("%s subscriptions expire tomorrow", len(expiring_subscriptions))
            for user_subscription in expiring_subscriptions:
                self.trying_recurring_payment(
                    user_id=user_subscription.get("user_id"),
                    subscription_id=user_subscription.get("subscription_id"),
                )
            return expiring_subscriptions
        except Exception as e:
            logger.exception(
                "Error when trying to check for expiring subscriptions: %s", e
            )

    def trying_recurring_payment(self, user_id: str, subscription_id) -> None:
        """Метод проведения рекурентного платежа"""
        try:
            self._request(
                method="POST",
                endpoint="/subscription/recurring_payment",
                data={"user_id": user_id, "subscription_id": subscription_id},
            )
        except Exception as e:
            logger.exception(
                "Error when trying recurring payment for user %s / subscription %s: %s",
                user_id,
                subscription_id,
                e,
            )

    def enable_preactive_user_subscriptions(self) -> None:
        """Метод активации предактивных подпискок"""
        try:
            self._request(method="GET", endpoint="/subscriptions/preactive/enable")
            logger.info("Preactive subscriptions on %s are enable", date.today())
        except Exception as e:
            logger.exception(
                "Error when trying to enable preactive user subscriptions : %s", e
            )


def start_scheduler() -> None:
    """Функция запуска планировщика"""
    logger.info("Scheduler is starting")
    scheduler = SchedulerService(billing_settings=settings)
    # TODO выставь везде правильное время старта задач, пока для тестирования оставлю эти
    schedule.every(5).seconds.do(scheduler.check_processing_orders)
    schedule.every(5).seconds.do(scheduler.check_processing_refunds)
    schedule.every(10).seconds.do(
        scheduler.check_expiring_active_subscriptions_automatic
    )
    schedule.every(10).seconds.do(scheduler.disable_expired_user_subscription)
    schedule.every(10).seconds.do(scheduler.enable_preactive_user_subscriptions)
    logger.info("Scheduler is running")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_scheduler()
