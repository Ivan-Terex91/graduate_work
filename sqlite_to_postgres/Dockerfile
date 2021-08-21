FROM python:latest

WORKDIR /etl
COPY ./requirements.txt ./requirements.txt
RUN pip install -r /etl/requirements.txt

COPY . .

CMD ["python",  "load_data.py"]
