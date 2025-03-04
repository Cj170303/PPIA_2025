import os
import io
import json
import random
import subprocess
import tempfile
import openai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from Prompt_Completion_V00 import Preguntas


app = Flask(__name__, static_folder='react_build')
CORS(app)

@app.route('/api/convert_latex', methods=['GET'])
def convert_latex_to_html():
    try:
        # Archivo .tex en la misma carpeta de app.py
        tex_path = os.path.join(os.getcwd(), "Preguntas.tex")
        html_path = os.path.join(os.getcwd(), "Preguntas.html")

        subprocess.run(["pandoc", tex_path, "-o", html_path], check=True)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return jsonify({"html": html_content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


History = [[
    {
        "id": 0,
        "responseChatbot": (
            "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
            "Por favor siéntase con toda la confianza de responder las preguntas según sus conocimientos.\n"
            "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo.\n"
            "Adicionalmente, si encuentra algún problema, háganoslo saber.\n\n"
            "Atentamente: Equipo de Pensando Problemas."
        )
    },
    {
        "id": 1,
        "responseChatbot": "Lo primero que hay que saber es: ¿en qué semana de universidad estás?"
    }
]]

history_path = "react_build/"
record = []
inicializador_id = 1
info = {}
success_fail = True
selected_theme = None
k = 140
user_week = None
allowed_temas = []

def get_available_temas(week):
    try:
        w = int(week)
    except:
        return []
    if w <= 2:
        return ["logica"]
    elif w <= 4:
        return ["logica", "lenguaje"]
    else:
        return ["logica", "lenguaje", "funciones"]

def load_history():
    global History, inicializador_id
    file_path = os.path.join(history_path, "History.json")
    inicializador_id = 1
    History = [[
        {
            "id": 0,
            "responseChatbot": (
                "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
                "Por favor siéntase con toda la confianza de responder las preguntas.\n"
                "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo.\n"
                "Adicionalmente, si encuentra algún problema, háganoslo saber.\n\n"
                "Atentamente: Equipo de Pensando Problemas."
            )
        },
        {
            "id": 1,
            "responseChatbot": "Lo primero que hay que saber es: ¿en qué semana de universidad estás?"
        }
    ]]
    with io.open(file_path, 'w', encoding='utf-8') as history_file:
        history_file.write(json.dumps(History))

def retrieve_temas_dif(temas_permitidos=None):
    temas = []
    difs = []
    for pid in Preguntas:
        if temas_permitidos is None or Preguntas[pid]['tema'] in temas_permitidos:
            if Preguntas[pid]['tema'] not in temas:
                temas.append(Preguntas[pid]['tema'])
            if Preguntas[pid]['dif'] not in difs:
                difs.append(Preguntas[pid]['dif'])
    return temas, difs

def fail_message():
    return (
        "Se ha equivocado en la elección de la respuesta correcta. "
        "A continuación se le mostrará un ejercicio de nivel menor o igual al realizado. "
        "¿ Desea Continuar ?"
    )

def success_message():
    return (
        "Ha acertado en la elección de la respuesta correcta. "
        "A continuación se le mostrará un ejercicio de nivel superior o igual al realizado. "
        "¿ Desea Continuar ?"
    )

def tail_message():
    global record
    if len(record) == 0:
        return "Ha finalizado la práctica.\nUsted realizó 0 ejercicios.\n\n¿ Desea reiniciar un quiz ?"

    themes = []
    difs_succeed = {}
    difs_failed = {}
    for rec_i in record:
        pid, was_correct = rec_i
        tema = Preguntas[pid]['tema']
        dif = Preguntas[pid]['dif']
        if tema not in themes:
            themes.append(tema)
        if was_correct:
            difs_succeed[dif] = difs_succeed.get(dif, 0) + 1
        else:
            difs_failed[dif] = difs_failed.get(dif, 0) + 1

    temas_str = ", ".join(str(t) for t in themes)

    def format_difs(difs_dict):
        lines = []
        for level, count in sorted(difs_dict.items()):
            lines.append(f"\t- {count} pregunta(s) del nivel {level}")
        return "\n".join(lines)

    summary_succeed = format_difs(difs_succeed)
    summary_failed = format_difs(difs_failed)

    rec_str = (
        f"El resumen de la práctica es el siguiente:\n"
        f"{summary_succeed}\n\n{summary_failed}"
    )

    return (
        f"Ha finalizado la práctica.\n"
        f"Usted realizó {len(record)} ejercicios.\n"
        f"El tema elegido fue {temas_str}.\n"
        f"{rec_str}\n¿ Desea reiniciar un quiz ?"
    )

def convert_latex_string_to_html(latex_str):
    """
    Convierte un string LaTeX a HTML usando Pandoc de forma temporal.
    Retorna el HTML como string.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp_tex:
            tmp_tex.write(latex_str.encode('utf-8'))
            tmp_tex_path = tmp_tex.name

        tmp_html_path = tmp_tex_path.replace(".tex", ".html")

        subprocess.run(["pandoc", tmp_tex_path, "-o", tmp_html_path], check=True)

        with open(tmp_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Limpieza opcional de archivos temporales
        os.remove(tmp_tex_path)
        os.remove(tmp_html_path)

        return html_content

    except Exception as e:
        return f"<p>Error al convertir LaTeX: {str(e)}</p>"

def init_question(selected_dif):
    global selected_theme
    candidates = [
        pid for pid in Preguntas
        if Preguntas[pid]['tema'] == selected_theme
        and Preguntas[pid]['dif'] == selected_dif
    ]
    return random.choice(candidates) if candidates else None

def call_question(pid):
    return Preguntas[pid]

def update_question(success_fail, pid):
    global info, selected_theme
    dificultad_actual = Preguntas[pid]['dif']
    same_tema = {k: v for k, v in Preguntas.items() if v['tema'] == selected_theme}

    candidates = []
    for qid, data in same_tema.items():
        if qid == pid:
            continue
        if success_fail:
            if data['dif'] >= dificultad_actual:
                candidates.append(qid)
        else:
            if data['dif'] <= dificultad_actual:
                candidates.append(qid)

    if not candidates:
        print("No hay más ejercicios disponibles.")
        return None
    return random.choice(candidates)

@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id, record, info, success_fail, selected_theme
    global user_week, allowed_temas

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400

        responseStudent = data.get('responseStudent', '')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question_txt = history[-1]['responseChatbot'] if history else ""

        # Caso 1: el chatbot preguntó la semana
        if "en qué semana de universidad estás" in question_txt:
            try:
                week = int(responseStudent.strip())
            except:
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': "Respuesta inválida. Ingrese un número correspondiente a la semana."
                }
                return jsonify({'message': resp})

            user_week = week
            allowed_temas = get_available_temas(week)
            (temas, difs) = retrieve_temas_dif(allowed_temas)

            temas_str = "\n".join(f"- {t}" for t in temas)
            difs_str = ", ".join(str(d) for d in difs)

            msg = (
                "Elige un tema y una dificultad dentro de la lista para empezar el quiz:\n\n"
                f"Temas:\n{temas_str}\n\n"
                f"Dificultades:\n{difs_str}\n\n"
                "Tu respuesta debe ser: tema dificultad (ej: logica 2)"
            )
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': msg
            }
            return jsonify({'message': resp})

        # Caso 2: selección de tema y dificultad
        if "Elige un tema y una dificultad" in question_txt:
            (temas, difs) = retrieve_temas_dif(allowed_temas)
            selected_dif = None
            for t in temas:
                if t.lower() in responseStudent.lower():
                    selected_theme = t
                    break
            for d in difs:
                if str(d) in responseStudent:
                    selected_dif = d
                    break

            if not selected_theme or not selected_dif:
                # Repetir el mensaje
                temas_str = "\n".join(f"- {t}" for t in temas)
                difs_str = ", ".join(str(d) for d in difs)
                msg = (
                    "No entendí tu respuesta.\n"
                    "Elige un tema y una dificultad dentro de la lista:\n\n"
                    f"Temas:\n{temas_str}\n\n"
                    f"Dificultades:\n{difs_str}\n\n"
                    "Ej: logica 2"
                )
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': msg
                }
                return jsonify({'message': resp})
            else:
                inicializador_id = init_question(selected_dif)
                if inicializador_id is None:
                    resp = {
                        'id': q_id,
                        'responseStudent': responseStudent,
                        'responseChatbot': "No hay ejercicios disponibles con ese tema/dificultad."
                    }
                    return jsonify({'message': resp})

                # Convertir enunciado LaTeX a HTML
                latex_str = Preguntas[inicializador_id]['enunciado']
                responseChatbot = convert_latex_string_to_html(latex_str)

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # Caso 3: Manejo de "¿Desea Continuar?" o "¿Desea reiniciar?"
        if "¿ Desea Continuar ?" in question_txt:
            if responseStudent.lower() in ["si", "sí", "yes"]:
                # Actualizar pregunta
                new_id = update_question(success_fail, inicializador_id)
                if new_id is None:
                    responseChatbot = tail_message()
                else:
                    inicializador_id = new_id
                    latex_str = Preguntas[inicializador_id]['enunciado']
                    responseChatbot = convert_latex_string_to_html(latex_str)
            elif responseStudent.lower() in ["no"]:
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea Continuar ?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        if "¿ Desea reiniciar un quiz ?" in question_txt:
            if responseStudent.lower() in ["si", "sí", "yes"]:
                record.clear()
                responseChatbot = "reinit"
            elif responseStudent.lower() in ["no"]:
                # Ejemplo: se podría mostrar una imagen de salida
                responseChatbot = os.path.join('Back_Python_New/exit.png')
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea reiniciar un quiz ?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # Caso 4: Evaluar la respuesta
        if not responseStudent.strip():
            return jsonify({'error': 'La pregunta está vacía'}), 400

        info = call_question(inicializador_id)
        success_fail = (responseStudent.strip().lower() in [r.lower() for r in info['res']])
        record.append((inicializador_id, success_fail))

        responseChatbot = success_message() if success_fail else fail_message()

        resp = {
            'id': q_id,
            'responseStudent': responseStudent,
            'responseChatbot': responseChatbot
        }
        return jsonify({'message': resp})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
