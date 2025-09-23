FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /api

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /api

COPY --from=builder /install /usr/local

COPY ./app ./app

EXPOSE 9002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9002"]