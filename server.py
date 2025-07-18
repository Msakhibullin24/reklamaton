from flask import Flask, request, jsonify
from pydantic import ValidationError
from validate import CharacterModel
import json

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_data():
    try:
        data = request.get_json()
        CharacterModel.model_validate(data)
        return jsonify({"status": "success", "message": "Данные валидны."})
    except ValidationError as e:
        return jsonify({"status": "error", "errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
