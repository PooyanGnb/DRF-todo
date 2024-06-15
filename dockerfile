FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE = 1
ENV PYTHONUNBUFFERED = 1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./core .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8001"]