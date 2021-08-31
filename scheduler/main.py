import logging
import time

import backoff
import schedule
from requests import request
from requests.exceptions import RequestException

from settings import Settings

settings = Settings()
logger = logging.getLogger("scheduler")
# TODO убери лишние логи


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
            print(processing_orders)
            logger.info(f"{len(processing_orders)} orders in processing")
            logger.info(f"orders{processing_orders}")
            for order in processing_orders:
                self.check_order_payment(order_external_id=order.get("external_id"))
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error when trying to check processing orders: {e}")

    def check_expiring_active_subscriptions_automatic(self):
        """Метод проверки всех активных подписок пользователей, срок действия которых истекает сегодня"""
        try:
            expiring_subscriptions = self._request(method="GET", endpoint="/subscriptions/automatic/active")
            logger.info(f"{len(expiring_subscriptions)} subscriptions expire today")
            logger.info(f"{expiring_subscriptions} subscriptions expire today")
            return expiring_subscriptions
        except Exception as e:
            logger.error(f"Error when trying to check for expiring subscriptions: {e}")

    def check_order_payment(self, order_external_id: str):
        """Метод проверки оплаты заказа"""
        try:
            order = self._request(method="GET", endpoint=f"/order/{order_external_id}/check")
            logger.info(f"order {order} ")
            print(order)
        except Exception as e:
            logger.error(f"Error when trying to check payment for order {order_external_id}: {e}")


if __name__ == '__main__':
    logger.info("Scheduler is starting")
    scheduler = SchedulerService(billing_settings=settings)

    schedule.every(5).seconds.do(scheduler.check_processing_orders)
    schedule.every(10).seconds.do(scheduler.check_expiring_active_subscriptions_automatic)
    logger.info("Scheduler is running")
    while True:
        schedule.run_pending()
        time.sleep(1)
