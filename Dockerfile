FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY pages/ pages/
COPY public/ public/
COPY styles/ styles/

RUN mkdir -p uploads/images uploads/pdfs

EXPOSE 8000

# Configuration comes from the environment (e.g. docker run --env-file .env)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
