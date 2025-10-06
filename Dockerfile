FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN rm requirements.txt

COPY code/* .
COPY config.yaml .

CMD ["python3", "-u", "main.py"]
