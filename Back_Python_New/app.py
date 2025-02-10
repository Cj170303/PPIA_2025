from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import random
import os
import json
import io
import openai

# Configuración de API (clave de OpenAI)
openai.api_key = "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"

app = Flask(__name__, static_folder='react_build')
CORS(app)

# Variables globales (histórico, control, registros)
History = [[
    {
        "id": 0,
        "responseChatbot": ("Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\nPor favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\nLos resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\nAdicionalmente, si encuentra algún problema o inconsistencia dentro de la App o con alguna pregunta, por favor, háganoslo saber.\n\nAtentamente: Equipo de Pensando Problemas.")
    }
]]
history_path = "react_build/"

record = []         # Registro de ejercicios realizados
inicializador_id = 1
info = {}           # Información ejercicio actual
success_fail = True # Control respuesta correcta/incorrecta
selected_theme = None
k = 140             # Variable de control (parámetro interno)

# Importar preguntas (estructura dict con identificadores, temas, niveles y respuestas)
from Prompt_Completion_V00 import Preguntas

def retrieve_temas_dif():
    temas = []
    difs = []
    for preg in Preguntas:
        if Preguntas[preg]['tema'] not in temas:
            temas.append(Preguntas[preg]['tema'])
        if Preguntas[preg]['dif'] not in difs:
            difs.append(Preguntas[preg]['dif'])
    return temas, difs

def load_history():
    global History, inicializador_id
    file_path = os.path.join(history_path, "History.json")
    (temas, difs) = retrieve_temas_dif()
    temas_str = "\t\t- " + ",\n\t\t- ".join(map(str, temas))
    difs_str = "\t\t- " + ", ".join(map(str, difs))
    list_temas_difs = f'''Elige un tema y una dificultad dentro de la lista para empezar el quiz:  
        Temas: 
{temas_str}

        Dificultades: 
{difs_str}

Tu respuesta debe estar en el formato: 
tema dificultad (ej: logica 2)

También puedes escribir: 'Hablar con IA' para resolver preguntas de lógica matemática.'''
    inicializador_id = 1
    if os.path.exists(file_path):
        History[0].append({'id': 1, 'responseChatbot': list_temas_difs})
        with io.open(file_path, 'w', encoding='utf-8') as history_file:
            history_file.write(json.dumps(History))
    else:
        with io.open(file_path, 'w', encoding='utf-8') as history_file:
            history_file.write(json.dumps([[]]))

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

# Función auxiliar para obtener respuesta desde API OpenAI (ChatGPT)
def get_chatgpt_response(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="text-moderation-latest",
            messages=[
                {"role": "system", "content": ("Eres asistente inteligencia artificial. "
                                                 "Responde cualquier pregunta formulada.")},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )
        chatbot_response = response['choices'][0]['message']['content']
        return chatbot_response
    except Exception as e:
        return f"Error en llamada a IA: {str(e)}"

# Ruta específica para modo IA (comunicación directa con ChatGPT)
@app.route('/api/chatgpt', methods=['POST'])
def chatgpt_route():
    data = request.get_json()
    if not data or not data.get('responseStudent') or data.get('responseStudent').isspace():
        return jsonify({'error': 'La pregunta está vacía'}), 400
    user_message = data.get('responseStudent')
    # Verificar comando para salir del modo IA
    if "salir de la ia" in user_message.lower() or "volver al quiz" in user_message.lower():
        # Recuperación de temas y dificultades
        (temas, difs) = retrieve_temas_dif()

        # Construcción de las cadenas formateadas sin incluir secuencias de escape directamente en el f-string
        temas_list_str = ",\n\t- ".join(map(str, temas))
        difs_list_str = ", ".join(map(str, difs))

        # Construcción del mensaje de selección de tema y dificultad utilizando las variables previamente definidas
        list_temas_difs = f'''Elige un tema y una dificultad dentro de la lista para empezar el quiz:  
                Temas: 
        \t- {temas_list_str}

                Dificultades: 
        \t- {difs_list_str}

        Tu respuesta debe estar en el formato: 
        tema dificultad (ej: logica 2)

        También puedes escribir: 'Hablar con IA' para resolver preguntas que tenga.'''
        return jsonify({'response': selected_instructions})
    chatbot_response = get_chatgpt_response(user_message)
    return jsonify({'response': chatbot_response})

# Ruta principal para procesamiento de preguntas y respuestas
@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id, record, info, success_fail, selected_theme
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400
        responseStudent = data.get('responseStudent')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question = history[-1]['responseChatbot'] if history else ""
        
        # Flujo: conversación en modo IA
        if "¡bienvenido a la ia!" in question.lower():
            if responseStudent and ("salir de la ia" in responseStudent.lower() or "volver al quiz" in responseStudent.lower()):
                temas, difs = retrieve_temas_dif()
                temas_join = ",\n\t- ".join(map(str, temas))
                difs_join = ", ".join(map(str, difs))
                selected_instructions = f'''Elige un tema y una dificultad dentro de la lista para empezar el quiz:  
                            Temas: 
                    \t- {temas_join}

                            Dificultades: 
                    \t- {difs_join}

                    Tu respuesta debe estar en el formato: 
                    tema dificultad (ej: logica 2)

                    También puedes escribir: 'Hablar con IA' para resolver preguntas que tenga.'''
                responseChatbot = selected_instructions
                response = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': responseChatbot
                }
                return jsonify({'message': response})
            # Evaluar entrada en modo IA (evitar mensaje vacío)
            if not responseStudent or responseStudent.isspace():
                return jsonify({'error': 'La pregunta está vacía'}), 400
            chatbot_response = get_chatgpt_response(responseStudent)
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': chatbot_response
            }
            return jsonify({'message': response})
        
        # Flujo: iniciar conversación con IA
        if responseStudent and "hablar con ia" in responseStudent.lower():
            responseChatbot = "¡Bienvenido a la IA! Puedes hacerme cualquier pregunta."
            response = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': response})
        
        # Flujo: selección de tema y dificultad para quiz
        if "Elige un tema y una dificultad" in question:
            (temas, difs) = retrieve_temas_dif()
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
                responseChatbot = tail_message()
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
