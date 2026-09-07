FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# botasaurus can chromium + deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-liberation libnss3 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[worker,postgres]"
COPY src ./src

EXPOSE 8000
CMD ["uvicorn", "app.main:api", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
