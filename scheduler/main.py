import logging
import time
from datetime import date

import backoff
import schedule
from requests import request
from requests.exceptions import RequestException

from settings import Settings

settings = Settings()
logger = logging.getLogger("scheduler")


class SchedulerService:
    """Класс для работы планировщика"""

    def __init__(self, billing_settings: Settings):
        self.billing_api_url = billing_settings.BILLING_API_URL
        self.base_endpoint = billing_settings.BILLING_API_BASE_ENDPOINT

    @backoff.on_exception(
        exception=RequestException,
        wait_gen=backoff.expo,
        max_time=30,
        logger=logger
    )
    def _request(
            self, method: str, endpoint: str, headers: dict = None, data: dict = None
    ):
        response = request(
            method=method,
            url=f"{self.billing_api_url}{self.base_endpoint}{endpoint}",
            headers=headers,
            data=data,
        )
        return response.json()

    def check_processing_orders(self):
        """Метод проверки оплаты заказов в обработке"""
        try:
            processing_orders = self._request(method="GET", endpoint="/orders/processing")
            logger.info(f"{len(processing_orders)} orders in processing")
            for order in processing_orders:
                self.check_order_payment(order_external_id=order.get("external_id"))
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error when trying to check processing orders: {e}")

    def check_order_payment(self, order_external_id: str) -> None:
        """Метод проверки оплаты заказа"""
        try:
            self._request(method="GET", endpoint=f"/order/{order_external_id}/check")
        except Exception as e:
            logger.error(f"Error when trying to check payment for order {order_external_id}: {e}")

    def check_processing_refunds(self) -> None:
        """Метод проверки проведения возвратов в обработке"""
        try:
            processing_refunds_orders = self._request(method="GET", endpoint="/refunds/processing")
            logger.info(f"{len(processing_refunds_orders)} refunds in processing")
            for refund_order in processing_refunds_orders:
                self.check_refund_execution(refund_external_id=refund_order.get("external_id"))
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error when trying to check processing refunds: {e}")

    def check_refund_execution(self, refund_external_id: str):
        """Метод проверки выполнения возврата"""
        try:
            self._request(method="GET", endpoint=f"/refund/{refund_external_id}/check")
        except Exception as e:
            logger.error(f"Error when trying to check refund execution {refund_external_id}: {e}")

    def disable_expired_user_subscription(self) -> None:
        """Метод отключает все истёкшие подписки пользователя"""
        try:
            self._request(method="GET", endpoint="/subscriptions/expired/disable")
            logger.info(f"Expired subscriptions on {date.today()} are disabled")
        except Exception as e:
            logger.error(f"Error when trying to disable expired user subscriptions : {e}")

    def check_expiring_active_subscriptions_automatic(self):
        """Метод проверки всех активных подписок пользователей, срок действия которых истекает сегодня"""
        try:
            expiring_subscriptions = self._request(method="GET", endpoint="/subscriptions/automatic/active")
            logger.info(f"{len(expiring_subscriptions)} subscriptions expire today")
            return expiring_subscriptions
        except Exception as e:
            logger.error(f"Error when trying to check for expiring subscriptions: {e}")


if __name__ == '__main__':
    logger.info("Scheduler is starting")
    scheduler = SchedulerService(billing_settings=settings)
    # TODO выставь везде правильное время старта задач
    schedule.every(5).seconds.do(scheduler.check_processing_orders)
    schedule.every(5).seconds.do(scheduler.check_processing_refunds)
    schedule.every(10).seconds.do(scheduler.check_expiring_active_subscriptions_automatic)
    schedule.every(10).seconds.do(scheduler.disable_expired_user_subscription)
    logger.info("Scheduler is running")
    while True:
        schedule.run_pending()
        time.sleep(1)
