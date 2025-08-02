FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN rm requirements.txt

COPY main.py .

RUN mkdir data

RUN echo '{}' > /data/last_resp.json


CMD ["python3", "main.py"]
