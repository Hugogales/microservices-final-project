FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY requirements.txt .

EXPOSE 5004

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"] 