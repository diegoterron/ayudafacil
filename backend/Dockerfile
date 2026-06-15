FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegador Chromium de Playwright y sus dependencias de Linux
RUN playwright install --with-deps chromium

# Copiar el código del backend
COPY . .

# Exponer el puerto del Backend
EXPOSE 8000

# Arrancar la aplicación FastAPI usando uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
