import os
import io
import json
import random
import subprocess
import tempfile
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from Prompt_Completion_V00 import Preguntas  # Debe tener 'week' en cada pregunta



app = Flask(__name__, static_folder='react_build')
CORS(app)

# ---------------------------------------------------------------------------------
# Ruta opcional para convertir un archivo .tex completo a HTML (vía Pandoc)
# ---------------------------------------------------------------------------------
@app.route('/api/convert_latex', methods=['GET'])
def convert_latex_to_html():
    try:
        tex_path = os.path.join(os.getcwd(), "Preguntas.tex")
        html_path = os.path.join(os.getcwd(), "Preguntas.html")
        subprocess.run(["pandoc", tex_path, "-o", html_path], check=True)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return jsonify({"html": html_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------------
# Variables globales
# ---------------------------------------------------------------------------------
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
record = []            # Registro de (id_pregunta, acierto?)
inicializador_id = 1   # ID de la pregunta actual
info = {}              # Info de la pregunta actual
success_fail = True
selected_theme = None
user_week = None

# ---------------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------------
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
    num_exercises = len(record)
    ejercicio_text = "ejercicio" if num_exercises == 1 else "ejercicios"
    if num_exercises == 0:
        return "Ha finalizado la práctica.\nUsted realizó 0 ejercicios.\n\n¿ Desea reiniciar un quiz ?"

    themes = []
    difs_succeed = {}
    difs_failed = {}

    for (pid, was_correct) in record:
        tema = Preguntas[pid]['tema']
        dif = Preguntas[pid]['dif']
        if tema not in themes:
            themes.append(tema)
        if was_correct:
            difs_succeed[dif] = difs_succeed.get(dif, 0) + 1
        else:
            difs_failed[dif] = difs_failed.get(dif, 0) + 1

    temas_str = ", ".join(str(t) for t in themes)
    total_acertadas = sum(difs_succeed.values())
    total_falladas = sum(difs_failed.values())
    acertadas_text = "acertada" if total_acertadas == 1 else "acertadas"
    falladas_text = "fallada" if total_falladas == 1 else "falladas"

    def format_difs(difs_dict):
        lines = []
        for level, count in sorted(difs_dict.items()):
            pregunta_text = "pregunta" if count == 1 else "preguntas"
            lines.append(f"\t- {count} {pregunta_text} del nivel {level}")
        return "\n".join(lines)

    summary_succeed = format_difs(difs_succeed)
    summary_failed = format_difs(difs_failed)
    rec_str = (
        f"Aquí se encuentra el resumen de la práctica:\n\n"
        f"Usted ha acertado ({total_acertadas} {acertadas_text}):\n{summary_succeed}\n\n"
        f"Usted ha fallado ({total_falladas} {falladas_text}):\n{summary_failed}"
    )

    return (
        f"Ha finalizado la práctica.\n"
        f"Ha completado todos los ejercicios disponibles con los parámetros ingresados.\n"
        f"Usted realizó {num_exercises} {ejercicio_text} y el tema elegido fue {temas_str}.\n\n"
        f"{rec_str}\nSi desea reiniciar el quiz, escriba: reiniciar"
        f"\n\n Espero haber ayudado en tu aprendizaje, nos vemos en la próxima práctica libre."
    )



def convert_latex_string_to_html(latex_str):
    """
    Convierte un string LaTeX a HTML usando Pandoc de forma temporal.
    Retorna el HTML como string.
    """
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp_tex:
            tmp_tex.write(latex_str.encode('utf-8'))
            tmp_tex_path = tmp_tex.name

        tmp_html_path = tmp_tex_path.replace(".tex", ".html")

        subprocess.run(["pandoc", tmp_tex_path, "-o", tmp_html_path], check=True)

        with open(tmp_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        os.remove(tmp_tex_path)
        os.remove(tmp_html_path)

        return html_content
    except Exception as e:
        return f"<p>Error al convertir LaTeX: {str(e)}</p>"

# ---------------------------------------------------------------------------------
# Filtrado de temas disponibles según la semana
# ---------------------------------------------------------------------------------
def get_available_temas(week):
    """
    Retorna la lista de temas que aparecen en preguntas con week <= user_week.
    """
    valid_temas = set()
    for pid, data in Preguntas.items():
        if data['week'] <= week:
            valid_temas.add(data['tema'])
    return sorted(valid_temas)

def retrieve_difs_for_temas(temas, week):
    """
    Retorna las dificultades disponibles para las 'temas' indicadas,
    solo de preguntas con week <= user_week.
    """
    difs = set()
    for pid, data in Preguntas.items():
        if data['tema'] in temas and data['week'] <= week:
            difs.add(data['dif'])
    return sorted(difs)

def init_question(selected_dif):
    """
    Elige una pregunta al azar del tema 'selected_theme' y la dificultad 'selected_dif',
    filtrando también por 'week' <= user_week.
    """
    global selected_theme, user_week
    candidates = [
        pid for pid in Preguntas
        if Preguntas[pid]['tema'] == selected_theme
        and Preguntas[pid]['dif'] == selected_dif
        and Preguntas[pid]['week'] <= user_week
    ]
    return random.choice(candidates) if candidates else None

def call_question(pid):
    return Preguntas[pid]

def update_question(success_fail, pid):
    global selected_theme, user_week
    dificultad_actual = Preguntas[pid]['dif']
    same_tema = {
        qid: data for qid, data in Preguntas.items()
        if data['tema'] == selected_theme and data['week'] <= user_week
    }

    candidates = []
    for qid, data in same_tema.items():
        if qid == pid:
            continue
        # Excluir ejercicios que ya hayan sido respondidos correctamente
        if any(r[0] == qid and r[1] for r in record):
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
    global user_week

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400

        responseStudent = data.get('responseStudent', '')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question_txt = history[-1]['responseChatbot'] if history else ""

        if responseStudent.strip().lower() == "reiniciar":
            record.clear()
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': "reinit"
            }
            return jsonify({'message': resp})

        # 1. El chatbot preguntó la semana
        if "en qué semana de universidad estás" in question_txt:
            try:
                week = int(responseStudent.strip())
            except:
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': "Respuesta inválida. Ingrese un número de semana."
                }
                return jsonify({'message': resp})

            user_week = week

            # Filtrar temas según las preguntas con week <= user_week
            allowed_temas = get_available_temas(week)
            # Dificultades para esos temas
            difs = retrieve_difs_for_temas(allowed_temas, week)

            if not allowed_temas or not difs:
                msg = (
                    "No hay preguntas disponibles para tu semana.\n"
                    f"Semana: {week}\n"
                    "¿Deseas reiniciar un quiz?"
                )
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': msg
                }
                return jsonify({'message': resp})

            temas_str = "\n".join(f"- {t}" for t in allowed_temas)
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

        # 2. Selección de tema y dificultad
        if "Elige un tema y una dificultad" in question_txt:
            # Reconstruimos la lista de temas y difs disponibles
            # en base a la semana del usuario
            allowed_temas = get_available_temas(user_week)
            difs = retrieve_difs_for_temas(allowed_temas, user_week)

            selected_dif = None
            found_theme = None

            for t in allowed_temas:
                if t.lower() in responseStudent.lower():
                    found_theme = t
                    break
            for d in difs:
                if str(d) in responseStudent:
                    selected_dif = d
                    break

            if not found_theme or not selected_dif:
                temas_str = "\n".join(f"- {t}" for t in allowed_temas)
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

            global selected_theme
            selected_theme = found_theme

            inicializador_id = init_question(selected_dif)
            if inicializador_id is None:
                temas_str = "\n".join(f"- {t}" for t in allowed_temas)
                difs_str = ", ".join(str(d) for d in difs)
                msg = (
                    "No hay ejercicios disponibles con tema/dificultad indicados.\n"
                    "Elija tema y dificultad dentro de la lista disponible:\n\n"
                    f"Temas:\n{temas_str}\n\n"
                    f"Dificultades:\n{difs_str}\n\n"
                    "Ejemplo: logica 2"
                )
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': msg
                }
                return jsonify({'message': resp})

            latex_str = Preguntas[inicializador_id]['enunciado']
            responseChatbot = convert_latex_string_to_html(latex_str)

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # 3. Manejo de "¿Desea Continuar?" o "¿Desea reiniciar?"
        if "¿ Desea Continuar ?" in question_txt:
            if responseStudent.lower() in ["si", "sí", "yes"]:
                new_id = update_question(success_fail, inicializador_id)
                if new_id is None:
                    responseChatbot = (
                        "Lamentablemente no hay más preguntas, ya completó todos los ejercicios posibles con los parámetros ingresados.\n\n"
                        + tail_message()
                    )

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
                responseChatbot = os.path.join('react_build','static', 'Images', 'exit.png')
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea reiniciar un quiz ?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # 4. Evaluar la respuesta
        if not responseStudent.strip():
            return jsonify({'error': 'La pregunta está vacía'}), 400

        info = call_question(inicializador_id)
        # Chequeo de acierto
        normalized_response = normalize_answer(responseStudent)
        normalized_correct = [normalize_answer(r) for r in info['res']]
        success_fail = normalized_response in normalized_correct
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

def normalize_answer(answer):
    normalized = answer.strip().lower()
    normalized = re.sub(r"[\(\)\[\]\{\}]", "", normalized)
    return normalized.strip()

# ---------------------------------------------------------------------------------
if __name__ == '__main__':
    load_history()
    app.run(port=3001, debug=True)
