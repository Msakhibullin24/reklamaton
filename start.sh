#!/bin/bash

# Создаем venv, если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения venv..."
    python3 -m venv venv
fi

# Активируем venv и устанавливаем зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запускаем сервер
echo "Запуск сервера..."
python rag_server.py
