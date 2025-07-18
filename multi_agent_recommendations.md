# Рекомендации по созданию мультиагентной системы

Ваша текущая система валидации данных — это идеальная отправная точка для создания мультиагентной системы. Каждый валидированный JSON с описанием персонажа, по сути, является "паспортом" для одного агента. Вот как можно развить эту идею.

## Концепция: Сцена и Оркестратор

Основная идея заключается в том, чтобы рассматривать взаимодействие нескольких персонажей как **сцену**, которой управляет главный агент — **Оркестратор**.

*   **Агенты (Персонажи):** Это ваши "Пахомы". Каждый из них обладает своим характером, стилем речи и поведением, описанными в JSON. Они действуют автономно в рамках своей роли.
*   **Оркестратор:** Это "режиссер" сцены. Он не имеет собственного видимого персонажа. Его задачи:
    1.  Получать на вход сообщение от пользователя.
    2.  Анализировать контекст диалога.
    3.  Решать, какой из агентов должен ответить следующим.
    4.  Передавать слово этому агенту и следить за соблюдением общей логики сцены.

## Шаг 1: Модификация структуры данных для "Сцены"

Вам нужно будет определить новую структуру данных, которая может содержать несколько персонажей. Например, в `validate.py` можно добавить новую модель:

```python
# В файле validate.py

from typing import List

# ... (существующие модели CharacterModel, etc.)

class SceneModel(BaseModel):
    scene_name: str
    agents: List[CharacterModel] # Список агентов, участвующих в сцене
    # Можно добавить и другие параметры сцены, например, описание локации
```

Пример JSON для такой сцены будет выглядеть так:

```json
{
  "scene_name": "Диалог на гауптвахте",
  "agents": [
    {
      "characterData": {
        "general": { "name": "Пахом" },
        "...": "..."
      }
    },
    {
      "characterData": {
        "general": { "name": "Братишка" },
        "...": "..."
      }
    }
  ]
}
```

## Шаг 2: Создание Оркестратора

Создайте новый файл, например, `orchestrator.py`. В нем будет класс `Orchestrator`.

```python
# В файле orchestrator.py
import google.generativeai as genai # или другая LLM

class Orchestrator:
    def __init__(self, scene_data):
        self.scene = scene_data
        self.agents = {agent.characterData.general.name: agent for agent in scene_data.agents}
        self.history = []
        # Здесь можно инициализировать LLM для Оркестратора
        self.llm = genai.GenerativeModel('gemini-1.5-flash')

    def get_next_speaker(self, user_input):
        # Это ключевая логика.
        # Оркестратор "думает", кто должен ответить.
        prompt = f"""
        История диалога: {self.history}
        Сообщение пользователя: "{user_input}"
        Участники сцены: {list(self.agents.keys())}
        
        Кто из участников должен ответить следующим? Назови только имя.
        """
        # Ответ от LLM будет, например, "Пахом"
        next_speaker_name = self.llm.generate_content(prompt).text.strip()
        return next_speaker_name

    def run_turn(self, user_input):
        self.history.append(f"Пользователь: {user_input}")
        
        speaker_name = self.get_next_speaker(user_input)
        
        # Здесь логика генерации ответа от выбранного агента
        # (можно использовать отдельную LLM для каждого агента с его "паспортом")
        agent_response = f"[{speaker_name}]: ...генерирует ответ в своем стиле..."
        
        self.history.append(agent_response)
        return agent_response
```

## Шаг 3: Обновление сервера

В `server.py` нужно добавить новый эндпоинт, например, `/run_scene`, который будет принимать JSON сцены, валидировать его с помощью `SceneModel` и запускать Оркестратор.

```python
# В файле server.py
from flask import request, jsonify
from validate import SceneModel # импортируем новую модель
from orchestrator import Orchestrator

# ...

@app.route('/run_scene', methods=['POST'])
def run_scene():
    try:
        # Валидация данных сцены
        scene_data = SceneModel.model_validate(request.get_json())
        
        # Создание и запуск Оркестратора
        orchestrator = Orchestrator(scene_data)
        
        # Для примера просто вернем подтверждение
        # В реальном приложении здесь начнется цикл диалога
        return jsonify({
            "status": "success", 
            "message": f"Сцена '{scene_data.scene_name}' с агентами {list(orchestrator.agents.keys())} успешно запущена."
        }), 200
        
    except ValidationError as e:
        return jsonify({"status": "error", "errors": e.errors()}), 400

```

## Итог

Таким образом, вы расширяете вашу систему от валидации одного персонажа до управления целой сценой с несколькими, сохраняя при этом строгую структуру и логику.
