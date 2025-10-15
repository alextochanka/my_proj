# Используем базовый образ Python
FROM python:3.11-slim-buster

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /usr/src/app

# Копируем ВСЕ файлы из текущего каталога (.) в рабочую директорию (/usr/src/app)
COPY . .

# Устанавливаем требуемые библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение
CMD ["python", "main.py"]