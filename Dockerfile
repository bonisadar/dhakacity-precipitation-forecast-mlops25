# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Use uvicorn to bind to 0.0.0.0 and $PORT
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

