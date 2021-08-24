# Format code
.PHONY: fmt
fmt:
	black .
	isort .

# Copy env file
copy_env_file:
	cp .env.sample .env