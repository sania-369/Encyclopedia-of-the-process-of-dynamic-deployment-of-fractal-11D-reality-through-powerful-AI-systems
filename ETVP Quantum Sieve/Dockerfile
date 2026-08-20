# Базовый легковесный образ с Python
FROM python:3.10-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код генератора и сервер
COPY "ETVP-CSPRNG v1.0.py" ./ETVP_CSPRNG_v1_0.py
COPY server.py .

# Открываем порт для внешних запросов
EXPOSE 8000

# Команда для запуска сервера
CMD ["python", "server.py"]
