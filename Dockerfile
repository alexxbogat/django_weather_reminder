FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "DjangoWeatherReminder.wsgi:application", "--bind", "0.0.0.0:8000"]