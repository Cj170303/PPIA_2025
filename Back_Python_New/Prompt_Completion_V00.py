#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: Implementación Prompt/Completion V00
# Por: Mateo Alejandro Rodríguez Ramírez
#----------------------------------------------------------#

Preguntas = {
    1:  {'res':['c'], 'dif':1, 'tema':'logica'},
    2:  {'res':['a'], 'dif':2, 'tema':'logica'},
    3:  {'res':['b'], 'dif':2, 'tema':'logica'},
    4:  {'res':['d'], 'dif':1, 'tema':'logica'},
    5:  {'res':['a'], 'dif':1, 'tema':'logica'},
    6:  {'res':['c'], 'dif':2, 'tema':'logica'},
    7:  {'res':['b','c'], 'dif':2, 'tema':'logica'},
    8:  {'res':['b','d'], 'dif':2, 'tema':'logica'},
    9:  {'res':['c','e'], 'dif':3, 'tema':'logica'},
    10: {'res':['d'], 'dif':1, 'tema':'lenguaje'},
    11: {'res':['c'], 'dif':1, 'tema':'lenguaje'},
    12: {'res':['a'], 'dif':1, 'tema':'lenguaje'},
    13: {'res':['b'], 'dif':1, 'tema':'lenguaje'},
    14: {'res':['c'], 'dif':1, 'tema':'lenguaje'},
    15: {'res':['b'], 'dif':2, 'tema':'lenguaje'},
    16: {'res':['a'], 'dif':2, 'tema':'lenguaje'},
    17: {'res':['d'], 'dif':1, 'tema':'lenguaje'},
    18: {'res':['c'], 'dif':2, 'tema':'lenguaje'},
    19: {'res':['a'], 'dif':1, 'tema':'lenguaje'},
    20: {'res':['d'], 'dif':3, 'tema':'lenguaje'},
    21: {'res':['b'], 'dif':2, 'tema':'lenguaje'}, 
    22: {'res':['c'], 'dif':2, 'tema':'lenguaje'},  
    23: {'res':['c'], 'dif':2, 'tema':'lenguaje'},  
    24: {'res':['b'], 'dif':3, 'tema':'lenguaje'},  
    25: {'res':['c'], 'dif':2, 'tema':'lenguaje'}, 
    26: {'res':['b'], 'dif':3, 'tema':'lenguaje'},  
    27: {'res':['c'], 'dif':3, 'tema':'lenguaje'}, 
    28: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    29: {'res':['c'], 'dif':1, 'tema':'lenguaje'}, 
    30: {'res':['b'], 'dif':1, 'tema':'lenguaje'}, 
    31: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    32: {'res':['b'], 'dif':1, 'tema':'lenguaje'}, 
    33: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    34: {'res':['c'], 'dif':1, 'tema':'lenguaje'},  
    35: {'res':['a'], 'dif':2, 'tema':'lenguaje'},  
    36: {'res':['a'], 'dif':1, 'tema':'lenguaje'}, 
    37: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    38: {'res':['a'], 'dif':1, 'tema':'lenguaje'}, 
    39: {'res':['a'], 'dif':2, 'tema':'lenguaje'},  
    40: {'res':['a'], 'dif':3, 'tema':'lenguaje'},  
    41: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    42: {'res':['c'], 'dif':1, 'tema':'lenguaje'},  
    43: {'res':['a'], 'dif':1, 'tema':'lenguaje'},  
    44: {'res':['b'], 'dif':1, 'tema':'lenguaje'},  
    45: {'res':['b'], 'dif':2, 'tema':'lenguaje'},  
    46: {'res':['d'], 'dif':1, 'tema':'funciones'}, 
    47: {'res':['b'], 'dif':1, 'tema':'funciones'}, 
    48: {'res':['b'], 'dif':2, 'tema':'funciones'},  
    49: {'res':['c'], 'dif':3, 'tema':'funciones'}, 
    50: {'res':['b'], 'dif':3, 'tema':'funciones'}   
}

#Las preguntas de "funciones", no son de funciones, es una prueba nada más

