import os
import uuid
import pathlib
from flask import Flask, request, jsonify
from pydantic import ValidationError
from validate import CharacterModel
import google.generativeai as genai

# Импорты для RAG
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Конфигурация ---
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAy817y7DirgpWnMPS6t5ps-6Ui2pFAMys")
if API_KEY == "AIzaSyAy817y7DirgpWnMPS6t5ps-6Ui2pFAMys":
    print("ПРЕДУПРЕЖДЕНИЕ: Не найден ключ GEMINI_API_KEY. Используется ключ-заглушка.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

app = Flask(__name__)

# Простое внутрипроцессное хранилище для сессий.
# Векторные базы будут храниться на диске.
SESSIONS = {}
VECTOR_STORE_DIR = pathlib.Path("./vector_stores")
VECTOR_STORE_DIR.mkdir(exist_ok=True) # Создаем директорию, если ее нет

def create_character_prompt(character_data, rag_context, user_message):
    # Эта функция остается почти без изменений
    prompt = f"""
Ты — актер, который должен идеально сыграть роль персонажа. Вживись в роль, используя следующие данные.

### ПАСПОРТ ПЕРСОНАЖА (СТРОГИЕ ДАННЫЕ) ###
{character_data.model_dump_json(indent=2)}

"""
    if rag_context:
        prompt += f"""
### ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ (используй эту информацию для ответа) ###
{rag_context}

"""
    
    prompt += f"""
### ЗАДАЧА ###
Ответь на сообщение пользователя, полностью соответствуя образу персонажа, его манере речи и ИСПОЛЬЗУЯ предоставленный контекст из базы знаний.

Сообщение пользователя: "{user_message}"

Твой ответ:
"""
    return prompt

# --- РОУТ 1: Настройка персонажа и создание векторной базы ---
@app.route('/setup_character', methods=['POST'])
def setup_character():
    if 'character_json' not in request.form:
        return jsonify({"error": "Отсутствует обязательная часть 'character_json' в form-data."}), 400
    
    json_data_str = request.form['character_json']

    try:
        character_data = CharacterModel.model_validate_json(json_data_str)
    except ValidationError as e:
        return jsonify({"status": "error", "message": "JSON данные невалидны.", "errors": e.errors()}), 400

    session_id = str(uuid.uuid4())
    vector_store_path = VECTOR_STORE_DIR / f"{session_id}.faiss"

    # Обработка файла контекста и создание векторной базы
    if 'context_file' in request.files:
        file = request.files['context_file']
        if file.filename != '':
            try:
                print(f"Чтение файла {file.filename}...")
                file_content = file.read().decode('utf-8')
                
                # 1. Разделение текста на чанки
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000, 
                    chunk_overlap=100
                )
                documents = text_splitter.create_documents([file_content])
                print(f"Текст разделен на {len(documents)} документов.")

                # 2. Создание и сохранение векторной базы FAISS
                print("Создание векторной базы FAISS...")
                vector_store = FAISS.from_documents(documents, embeddings)
                vector_store.save_local(str(vector_store_path))
                print(f"Векторная база сохранена в {vector_store_path}")

            except Exception as e:
                return jsonify({"error": f"Ошибка при обработке файла и создании RAG: {e}"}), 500

    # Сохраняем данные персонажа в сессию
    SESSIONS[session_id] = {
        "character_data": character_data,
    }
    
    print(f"Персонаж '{character_data.characterData.general.name}' настроен. Session ID: {session_id}")
    
    return jsonify({"status": "success", "session_id": session_id})

# --- РОУТ 2: Общение с персонажем с использованием RAG ---
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
    vector_store_path = VECTOR_STORE_DIR / f"{session_id}.faiss"
    rag_context = ""

    # Поиск релевантного контекста в векторной базе
    if vector_store_path.exists():
        try:
            print(f"Загрузка векторной базы для сессии {session_id}...")
            vector_store = FAISS.load_local(str(vector_store_path), embeddings, allow_dangerous_deserialization=True)
            
            # Поиск 4 наиболее релевантных документов
            retriever = vector_store.as_retriever(search_kwargs={"k": 4})
            docs = retriever.invoke(user_message)
            
            # Формирование контекста из найденных документов
            rag_context = "\n\n---\n\n".join([doc.page_content for doc in docs])
            print(f"Найден релевантный контекст:\n{rag_context}")

        except Exception as e:
            print(f"Ошибка при работе с векторной базой: {e}")
            # Не прерываем работу, просто контекст будет пустым
    
    try:
        full_prompt = create_character_prompt(
            session_data["character_data"], 
            rag_context, 
            user_message
        )
        
        print(f"--- ИТОГОВЫЙ ПРОМПТ ДЛЯ СЕССИИ {session_id} ---")
        print(full_prompt)
        print("------------------------------------")
        
        response = model.generate_content(full_prompt)
        character_response = response.text
        
        return jsonify({"status": "success", "response": character_response})

    except Exception as e:
        return jsonify({"error": f"Ошибка при обращении к Gemini: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
