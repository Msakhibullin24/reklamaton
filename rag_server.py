import os
import uuid
from flask import Flask, request, jsonify
from pydantic import ValidationError
from validate import CharacterModel
import google.generativeai as genai

# --- Конфигурация ---
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAy817y7DirgpWnMPS6t5ps-6Ui2pFAMys")
if API_KEY == "AIzaSyAy817y7DirgpWnMPS6t5ps-6Ui2pFAMys":
    print("ПРЕДУПРЕЖДЕНИЕ: Не найден ключ GEMINI_API_KEY. Используется ключ-заглушка.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite')

app = Flask(__name__)

# Простое внутрипроцессное хранилище для сессий.
# В реальном приложении здесь может быть Redis или другая база данных.
SESSIONS = {}

def create_character_prompt(character_data, rag_context, user_message):
    # Эта функция остается без изменений
    prompt = f"""
Ты — актер, который должен идеально сыграть роль персонажа. Вживись в роль, используя следующие данные.

### ПАСПОРТ ПЕРСОНАЖА (СТРОГИЕ ДАННЫЕ) ###
{character_data.model_dump_json(indent=2)}

"""
    if rag_context:
        prompt += f"""
### ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ (ФРАЗЫ, ИСТОРИИ, МАНЕРА РЕЧИ) ###
{rag_context}

"""
    
    prompt += f"""
### ЗАДАЧА ###
Ответь на сообщение пользователя, полностью соответствуя образу персонажа, его манере речи и используя предоставленный контекст.

Сообщение пользователя: "{user_message}"

Твой ответ:
"""
    return prompt

# --- РОУТ 1: Настройка персонажа ---
@app.route('/setup_character', methods=['POST'])
def setup_character():
    if 'character_json' not in request.form:
        return jsonify({"error": "Отсутствует обязательная часть 'character_json' в form-data."}), 400
    
    json_data_str = request.form['character_json']

    try:
        character_data = CharacterModel.model_validate_json(json_data_str)
    except ValidationError as e:
        return jsonify({"status": "error", "message": "JSON данные невалидны.", "errors": e.errors()}), 400

    rag_context = ""
    if 'context_file' in request.files:
        file = request.files['context_file']
        if file.filename != '':
            try:
                rag_context = file.read().decode('utf-8')
            except Exception as e:
                return jsonify({"error": f"Не удалось прочитать файл: {e}"}), 400

    # Создаем уникальный ID для сессии
    session_id = str(uuid.uuid4())
    
    # Сохраняем данные персонажа в "базу данных"
    SESSIONS[session_id] = {
        "character_data": character_data,
        "rag_context": rag_context
    }
    
    print(f"Персонаж '{character_data.characterData.general.name}' настроен. Session ID: {session_id}")
    
    return jsonify({"status": "success", "session_id": session_id})

# --- РОУТ 2: Общение с персонажем ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'session_id' not in data or 'user_message' not in data:
        return jsonify({"error": "Требуются 'session_id' и 'user_message' в JSON-теле запроса."}), 400

    session_id = data['session_id']
    user_message = data['user_message']

    if session_id not in SESSIONS:
        return jsonify({"error": "Указанный session_id не найден."}), 404

    session_data = SESSIONS[session_id]
    
    try:
        full_prompt = create_character_prompt(
            session_data["character_data"], 
            session_data["rag_context"], 
            user_message
        )
        
        response = model.generate_content(full_prompt)
        character_response = response.text
        
        print(f"--- ПРОМПТ ДЛЯ СЕССИИ {session_id} ---")
        print(full_prompt)
        print("------------------------------------")
        
        # character_response = f"[ОТВЕТ ОТ GEMINI] Я, {session_data['character_data'].characterData.general.name}, отвечаю на '{user_message}'"

        return jsonify({"status": "success", "response": character_response})

    except Exception as e:
        return jsonify({"error": f"Ошибка при обращении к Gemini: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
