# Запуск тестов
1. Склонировать проект
2. Перейти в каталог /billing_api
3. Выполнить команду `python -m pytest -v`

# Запуск проекта
1. Склонировать проект
2. Скопировать переменные окружения командой `make copy_env_file`.
3. Запустить `docker-compose up -d --build`
4. Запустить `make init_admin_panel`, соберётся статика для админки и нужно будет ввести данные для создания суперпользователя

# Billing_API
Swagger - `http://127.0.0.1:8008/api/openapi`

# Auth
Swagger - `http://127.0.0.1:8001/`

# Administration service
`http://127.0.0.1:8000/admin/`


TODO 
1. Есть небольшая ошибка в логике, которая была поздно замечена, нужно её поправить. Она связана с рекурентными платежами, а именно с продлением подписки более одного раза.
2. Конечно, нужно добавить больше тестов, функциональных и интеграционных.
3. Сделать абстрактный класс для платёжных систем.