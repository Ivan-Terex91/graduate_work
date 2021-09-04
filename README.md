
# Запуск проекта
1. Скопировать переменные окружения командой `make copy_env_file`.
2. Запустить `docker-compose up -d --build`
3. Запустить `make init_admin_panel`, соберётся статика для админки и нужно будет ввести данные для создания суперпользователя

# Billing_API
Swagger - `http://127.0.0.1:8008/api/openapi`

# Auth
Swagger - `http://127.0.0.1:8001/`

# Administration service
`http://127.0.0.1:8000/admin/`

Ссылка на репозиторий https://github.com/Ivan-Terex91/graduate_work

P.S. Забыл на встрече показать и рассказать, есть ещё блок схемы в Miro с жизненными циклами оформления, отказа от подписки и рекурентные платежи.


[Исправления по ревью](https://github.com/Ivan-Terex91/graduate_work/pull/15)
[Начало функциональных тестов](https://github.com/Ivan-Terex91/graduate_work/pull/16)
