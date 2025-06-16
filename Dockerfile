FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]
