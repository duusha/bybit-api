# Используем официальный образ Python 3.9 (можно поменять при необходимости)
FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем весь проект в контейнер
COPY . /app

# Устанавливаем зависимости
RUN apt update
RUN apt upgrade -y
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Открываем порт (если в будущем понадобится API или WebSocket)
EXPOSE 8000

# Запускаем test_sock.py
CMD ["python", "test_sock.py"]

