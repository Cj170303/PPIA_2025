#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: Implementación Pipeline V00
# Por: Mateo Alejandro Rodríguez Ramírez
#----------------------------------------------------------#

# Cargue de Paquetes:

ruta = r'./'
import os
import random
import psutil
os.chdir(ruta)
os.listdir()

from Prompt_Completion_V00 import Preguntas
from PIL import Image

# Iniciales:
k = 140
emph = '#'+'-'*k+'#'

def init_message():
    print(emph)
    codigo = input('\nEscriba su Código de Estudiante: ')
    print(emph)
    return codigo

def head():
    head_message = emph+'\nUsted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó.\nPor favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\nLos resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\n\nAtentamente: Equipo de Pensando Problemas.\n'+emph
    print(head_message)

def tail(n):
    tail_message = '\n\n'+emph+'\nHa finalizado la práctica.\nUsted realizó {} ejercicios.\n'.format(n)+emph
    print(tail_message)

def ask_message():
    ask_msg = input('\n\nEscriba su respuesta: ')
    return ask_msg

def fail_message():
    fail_msg = '\n\nSe ha equivocado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel menor o igual al que realizó.\n\n'
    print(fail_msg)

def success_message():
    success_msg = '\n\nHa acertado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel superior o igual al que realizó.\n\n'
    print(success_msg)

def continuacion():
    continuar = input('\n¿Desea Continuar (yes:1,no:0)?: ')
    enter = (continuar=='1')
    return enter

def call_image(id): 
    img = Image.open('../../Preguntas/Preg_0{}.png'.format(id))
    img.show()

def call_question(id):
    return Preguntas[id]

def close_image():
    for proc in psutil.process_iter():
        print(proc)
        if proc.name() == "display":
            proc.kill()

def update_question(success_fail,info,inicializador_id):
    indices = []
    dificultad_actual = Preguntas[inicializador_id]['dif']
    for pregunta in Preguntas:
        if pregunta != inicializador_id:
            if success_fail:
                if info['dif']>= dificultad_actual:
                    indices.append(pregunta)
            else:
                if info['dif']<= dificultad_actual:
                    indices.append(pregunta)
    try:
        indice = random.choice(indices)
        return indice
    except:
        print('\nNo hay más ejercicios para que usted resuelva.\n')

#-------------------------------
# Corrida del programa

def program():
    record = []
    enter = True
    n = 0
    inicializador_id = 1
    while enter:
        if n==0: 
            head() # Mensaje de Bienvenida al programa.
        n+=1
        call_image(inicializador_id) # Muestra la pregunta.
        info = call_question(inicializador_id) # Obtiene la información de la pregunta.
        response = ask_message() # Pide la respuesta al estudiante.
        success_fail = response in info['res'] # Revisa si la respuesta es correcta o no.
        record.append((inicializador_id,success_fail)) #  
        if success_fail:
            success_message() # Mensaje de acierto en la respuesta
        else:
            fail_message() # Mensaje de fallo en la respuesta:
        #close_image() #Se cierra la imagen en cuestión.
        enter =continuacion() # Pregunta si se desea continuar, independiente de si acierta o no.
        inicializador_id = update_question(success_fail,info,inicializador_id) # Se actualiza a una nueva pregunta para que el estudiante resuelva.
        if enter==False: 
            tail(n) # Mensaje de Salida del programa.    
    return(record)

def run_program():
    nombre = init_message()
    puntaje = program()
    return({nombre:puntaje})

if False:
    for k in psutil.process_iter():
        k.name()
        if k.name()=='display':
            print('Hola')

run_program()






