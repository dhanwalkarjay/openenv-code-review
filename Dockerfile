FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements-runtime.txt ./requirements-runtime.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-runtime.txt

COPY backend ./backend
COPY env ./env
COPY frontend ./frontend

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
