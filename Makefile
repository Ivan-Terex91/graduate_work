# Format code
.PHONY: fmt
fmt:
	black .
	isort .