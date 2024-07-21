
FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["fastapi","dev", "api/main.py"]

EXPOSE 8000