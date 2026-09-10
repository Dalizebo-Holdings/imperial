# BaaS API Service
FROM python:3.12-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev curl

COPY baas/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "-m", "baas.runtime.server"]