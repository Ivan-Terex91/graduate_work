FROM python:latest

WORKDIR admin_pannel
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY . .


CMD ["bash", "django-entrypoint.sh"]
