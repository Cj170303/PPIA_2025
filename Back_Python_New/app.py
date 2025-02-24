from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import random
import os
import json
import io
import openai

app = Flask(__name__, static_folder='react_build')
CORS(app)

# Variables globales (histórico, control, registros)
History = [[
    {
        "id": 0,
        "responseChatbot": ("Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
                            "Por favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\n"
                            "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\n"
                            "Adicionalmente, si encuentra algún problema o inconsistencia dentro de la App o con alguna pregunta, por favor, háganoslo saber.\n\n"
                            "Atentamente: Equipo de Pensando Problemas.")
    },
    {
        "id": 1,
        "responseChatbot": "Lo primero que hay que saber es que semana de universidad estás"
    }
]]
history_path = "react_build/"

record = []         # Registro de ejercicios realizados
inicializador_id = 1
info = {}           # Información ejercicio actual
success_fail = True # Control respuesta correcta/incorrecta
selected_theme = None
k = 140             # Variable de control (parámetro interno)

# Variables globales adicionales para manejo de etapa y temas permitidos
user_week = None
allowed_temas = []  # Temas disponibles conforme a la semana

# Función que, según número de semana, retorna lista de temas permitidos
def get_available_temas(week):
    try:
        week = int(week)
    except Exception as e:
        return []
    if week <= 2:
        return ["logica"]
    elif week <= 4:
        return ["logica", "lenguaje"]
    else:
        return ["logica", "lenguaje", "funciones"]

# Importar preguntas (estructura dict con identificadores, temas, niveles y respuestas)
from Prompt_Completion_V00 import Preguntas

# Función modificada para extraer únicamente temas permitidos (si se provee filtro)
def retrieve_temas_dif(temas_permitidos=None):
    temas = []
    difs = []
    for preg in Preguntas:
        if temas_permitidos is None or Preguntas[preg]['tema'] in temas_permitidos:
            if Preguntas[preg]['tema'] not in temas:
                temas.append(Preguntas[preg]['tema'])
            if Preguntas[preg]['dif'] not in difs:
                difs.append(Preguntas[preg]['dif'])
    return temas, difs

def load_history():
    global History, inicializador_id
    file_path = os.path.join(history_path, "History.json")
    inicializador_id = 1
    # Se inicializa el historial con los dos mensajes deseados
    History = [[
        {
            "id": 0,
            "responseChatbot": ("Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
                                "Por favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\n"
                                "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\n"
                                "Adicionalmente, si encuentra algún problema o inconsistencia dentro de la App o con alguna pregunta, por favor, háganoslo saber.\n\n"
                                "Atentamente: Equipo de Pensando Problemas.")
        },
        {
            "id": 1,
            "responseChatbot": "Lo primero que hay que saber es que semana de universidad estás"
        }
    ]]
    with io.open(file_path, 'w', encoding='utf-8') as history_file:
        history_file.write(json.dumps(History))

def fail_message():
    return ("Se ha equivocado en la elección de la respuesta correcta. "
            "A continuación se le mostrará ejercicio de nivel menor o igual al realizado. "
            "¿ Desea Continuar ?")

def success_message():
    return ("Ha acertado en la elección de la respuesta correcta. "
            "A continuación se le mostrará ejercicio de nivel superior o igual al realizado. "
            "¿ Desea Continuar ?")

def tail_message():
    global record
    themes = []
    difs_succeed = {}
    difs_failed = {}
    if len(record) == 0:
        return "Ha finalizado la práctica.\nUsted realizó {} ejercicios.\n\n¿ Desea reiniciar un quiz ?".format(len(record))
    for rec in record:
        if Preguntas[rec[0]]['tema'] not in themes:
            themes.append(Preguntas[rec[0]]['tema'])
        if rec[1]:
            difs_succeed[Preguntas[rec[0]]['dif']] = difs_succeed.get(Preguntas[rec[0]]['dif'], 0) + 1
        else:
            difs_failed[Preguntas[rec[0]]['dif']] = difs_failed.get(Preguntas[rec[0]]['dif'], 0) + 1
    temas_str = ", ".join(map(str, themes))
    sorted_dict_succeed = dict(sorted(difs_succeed.items()))
    summary_succeed = "\n ".join(
        f"\t- {count} preguntas{'s' if count > 1 else ''} del nivel {level} logradas"
        for level, count in sorted_dict_succeed.items()
    )
    sorted_dict_failed = dict(sorted(difs_failed.items()))
    summary_failed = "\n ".join(
        f"\t- {count} preguntas{'s' if count > 1 else ''} del nivel {level} perdidas"
        for level, count in sorted_dict_failed.items()
    )
    rec_str = f"El resumen de la práctica es el siguiente: \n{summary_succeed}\n\n{summary_failed}"
    return ("Ha finalizado la práctica.\nUsted realizó {} ejercicios.\nEl tema elegido fue {}.\n{}\n¿ Desea reiniciar un quiz ?"
            .format(len(record), temas_str, rec_str))

def call_image(id):
    img = os.path.join('react_build', 'Images', f'Preg_0{id}.png')
    return img

def call_question(id):
    return Preguntas[id]

def init_question(selected_dif):
    global selected_theme
    indices = [preg for preg in Preguntas 
               if Preguntas[preg]['tema'] == selected_theme and Preguntas[preg]['dif'] == selected_dif]
    indice = random.choice(indices)
    return indice

def update_question(success_fail, inicializador_id):
    global info, selected_theme
    indices = []
    dificultad_actual = Preguntas[inicializador_id]['dif']
    filtered_preguntas = {key: value for key, value in Preguntas.items() if value['tema'] == selected_theme}
    for pregunta in filtered_preguntas:
        if pregunta != inicializador_id:
            if success_fail:
                if info['dif'] >= dificultad_actual:
                    indices.append(pregunta)
            else:
                if info['dif'] <= dificultad_actual:
                    indices.append(pregunta)
    try:
        indice = random.choice(indices)
        return indice
    except Exception as e:
        print("No hay más ejercicios disponibles.")
        return None

# Ruta principal para procesamiento de preguntas y respuestas
@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id, record, info, success_fail, selected_theme, user_week, allowed_temas
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400
        responseStudent = data.get('responseStudent')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question = history[-1]['responseChatbot'] if history else ""
        
        # Flujo: procesamiento de respuesta a la pregunta sobre la semana
        if "Lo primero que hay que saber es que semana de universidad estás" in question:
            try:
                week = int(responseStudent.strip())
            except Exception as e:
                responseChatbot = "Respuesta inválida. Ingrese un número correspondiente a la semana de universidad."
                response = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': responseChatbot
                }
                return jsonify({'message': response})
            user_week = week
            allowed_temas = get_available_temas(week)
            (temas, difs) = retrieve_temas_dif(allowed_temas)
            temas_str = "\t- " + "\n\t- ".join(map(str, temas))
            difs_str = "\t- " + ", ".join(map(str, difs))
            list_temas_difs = f'''Elige un tema y una dificultad dentro de la lista para empezar el quiz:  
    Temas: 
{temas_str}

    Dificultades: 
{difs_str}

Tu respuesta debe estar en el formato: 
tema dificultad (ej: logica 2)'''
            responseChatbot = list_temas_difs
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': response})
        
        # Flujo: selección de tema y dificultad para quiz
        if "Elige un tema y una dificultad" in question:
            (temas, difs) = retrieve_temas_dif(allowed_temas)
            selected_dif = None
            for tema in temas:
                if tema.lower() in responseStudent.lower():
                    selected_theme = tema
                    break
            for dif in difs:
                if str(dif) in responseStudent:
                    selected_dif = dif
                    break
            if selected_theme is None or selected_dif is None:
                temas_str = "\t- " + ",\n\t- ".join(map(str, temas))
                difs_str = "\t- " + ", ".join(map(str, difs))
                list_temas_difs = f'''Elige un tema y una dificultad dentro de la lista para empezar el quiz:  
    Temas: 
{temas_str}

    Dificultades: 
{difs_str}

Tu respuesta debe estar en el formato: 
tema dificultad (ej: logica 2)'''
                responseChatbot = "No entendí tu respuesta.\n" + list_temas_difs
            else:
                inicializador_id = init_question(selected_dif)
                responseChatbot = call_image(inicializador_id)
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': response})
        
        # Flujo: manejo de respuestas en quiz (continuar, reiniciar, evaluación)
        if "¿ Desea Continuar ?" in question:
            if responseStudent and ("si" in responseStudent.lower() or "yes" in responseStudent.lower()):
                inicializador_id = update_question(success_fail, inicializador_id)
                if inicializador_id is None:
                    responseChatbot = tail_message()
                else:
                    responseChatbot = call_image(inicializador_id)
            elif responseStudent and ("no" in responseStudent.lower()):
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea Continuar ?"
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': response})
        
        if "¿ Desea reiniciar un quiz ?" in question:
            if responseStudent and ("si" in responseStudent.lower() or "yes" in responseStudent.lower()):
                record = []
                responseChatbot = "reinit"
            elif responseStudent and ("no" in responseStudent.lower()):
                responseChatbot = os.path.join('react_build', 'Images', 'exit.png')
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea reiniciar un quiz ?"
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': response})
        
        # Flujo: evaluación respuesta ejercicio (quiz)
        if not responseStudent or responseStudent.isspace():
            return jsonify({'error': 'La pregunta está vacía'}), 400
        info = call_question(inicializador_id)
        success_fail = responseStudent in info['res']
        record.append((inicializador_id, success_fail))
        responseChatbot = success_message() if success_fail else fail_message()
        response = {
            'id': q_id,
            'responseStudent': responseStudent,
            'responseChatbot': responseChatbot
        }
        return jsonify({'message': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rutas para servir aplicación front-end (React)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    load_history()
    app.run(port=3001, debug=True)
