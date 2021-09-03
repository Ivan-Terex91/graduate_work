# Format code
.PHONY: fmt
fmt:
	black .
	isort .

# Copy env file
copy_env_file:
	cp .env.sample .env

# Collect static and create superuser in django admin
init_admin_panel:
	docker-compose exec admin-panel python manage.py collectstatic
	docker-compose exec admin-panel python manage.py createsuperuser
