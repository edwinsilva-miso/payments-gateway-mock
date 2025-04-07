FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Puerto en el que se ejecutará nuestra API
EXPOSE 8000

# Ejecutar con gunicorn para entornos de producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]