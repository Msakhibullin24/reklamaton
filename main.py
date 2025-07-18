import json
from server import app  # Импортируем наше Flask-приложение

def test_validation():
    """
    Тестирует эндпоинт /validate с помощью тестового клиента Flask.
    """
    # Создаем тестовый клиент
    client = app.test_client()

    # Загружаем НЕВАЛИДНЫЕ тестовые данные
    try:
        with open("invalid_character_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Ошибка: Файл invalid_character_data.json не найден.")
        return
    except json.JSONDecodeError:
        print("Ошибка: Не удалось декодировать JSON из файла invalid_character_data.json.")
        return

    print("Запуск теста валидации через тестовый клиент...")
    # Отправляем POST-запрос на /validate
    response = client.post('/validate', 
                           data=json.dumps(data), 
                           content_type='application/json')

    # Выводим результат
    print(f"Статус-код ответа: {response.status_code}")
    print("Тело ответа:")
    # response.data - это байтовая строка, декодируем ее в utf-8
    print(json.dumps(json.loads(response.data.decode('utf-8')), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_validation()
