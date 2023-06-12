
from flask import Flask, render_template
from flask_socketio import SocketIO 
import paho.mqtt.client as mqtt
import json
import threading
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import threading
import io
import base64


# Nueva instancia de Flask y SocketIO
app = Flask(__name__,static_folder='static')
socketio = SocketIO(app)

############################################################################################## 
#                                         VENTANA                                            #
############################################################################################## 


guardar_pulsado = False
predecirminutos = 0
referencia = ''

# función para obtener la referencia y cerrar la ventana
def obtener_referencia(event):
    global referencia
    referencia = entrada_referencia.get()

# Ventana principal
ventana = tk.Tk()
ventana.geometry("400x300")
ventana.configure(bg="#202020")

# Estilo
estilo = ttk.Style()
estilo.theme_use('clam')
estilo.configure('.', background="#202020", foreground='white')


# Etiqueta "predecir X minutos vista"
etiqueta_minutos_vista = tk.Label(ventana, text="Predecir X minutos vista:", font=('Helvetica', 14), fg='white', bg='#202020')
etiqueta_minutos_vista.pack(pady=10)
# Input "predecir a x minutos vista"
entrada_minutos_vista = tk.Entry(ventana, text="Predecir X minutos vista", font=('Helvetica', 14))
entrada_minutos_vista.pack(pady=10)
entrada_minutos_vista.focus() # Establecer el enfoque inicial en el cuadro de entrada

# Etiqueta "Guardar datos"
etiqueta_guardar = tk.Label(ventana, text="Guardar datos:", font=('Helvetica', 14), fg='white', bg='#202020')
etiqueta_guardar.pack()
# Variable del estado del checkbox
guardar_var = tk.IntVar()
# Checkbox "Guardar datos"
checkbox_guardar = tk.Checkbutton(ventana, variable=guardar_var, font=('Helvetica', 14), fg='white', bg='#202020')
checkbox_guardar.pack()

# Etiqueta "Introduce una nueva referencia"
etiqueta_referencia = tk.Label(ventana, text="Introduce una nueva referencia:", font=('Helvetica', 14), fg='white', bg='#202020')
etiqueta_referencia.pack(pady=10)
# Input de la referencia
entrada_referencia = tk.Entry(ventana, font=('Helvetica', 14))
entrada_referencia.pack(ipady=5)

# Función que verifica si la opción de guardar datos ha sido seleccionada
def on_check():
    global guardar_pulsado
    if guardar_var.get() == 1:
        guardar_pulsado = True
        etiqueta_referencia.pack(pady=10)
        entrada_referencia.pack(ipady=5)
    else:
        guardar_pulsado = False
        etiqueta_referencia.pack_forget()
        entrada_referencia.pack_forget()

checkbox_guardar.config(command=on_check)

# Función que registra la tecla "Enter" para enviar los datos
def on_enter(event):
    if guardar_var.get() == 1:
        global referencia
        global predecirminutos
        referencia = entrada_referencia.get()
        predecirminutos =  entrada_minutos_vista.get()
        predecirminutos =  float(predecirminutos)

    else:
        predecirminutos=  entrada_minutos_vista.get()
        predecirminutos =  float(predecirminutos)
    ventana.destroy()

entrada_minutos_vista.bind('<Return>', on_enter)
entrada_referencia.bind('<Return>', on_enter)

on_check()
ventana.mainloop()



############################################################################################## 
#                                        CONFIG DE MYSQL                                     #
############################################################################################## 
import mysql.connector
conexion = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  database="tfg"
)
cursor = conexion.cursor()

############################################################################################## 
#                                         PREDICCIÓN                                         #
############################################################################################## 

# Cálculo de los datos necesarios en base a la ventana
valoresFuturos = (predecirminutos * 60) / 0.2 
valoresFuturos = int(valoresFuturos)
if predecirminutos == 0:
    datosparaprediccion = 2000
else:
    datosparaprediccion = valoresFuturos * 2
    datosparaprediccion = int(datosparaprediccion)
print(predecirminutos)
print(valoresFuturos)
print(datosparaprediccion)


from queue import Queue
result_queue1 = Queue()
result_queue2 = Queue()

#para evitar que al estar en un hilo secundario la generacion del plot, se pare el programa
import matplotlib
matplotlib.use('Agg')

def predecir(data, result_queue):
    global resultado

    df2 = data
    df2 = pd.DataFrame(df2)
    
    dataset_total = df2.iloc[:, 1] 

    # Escalado de los datos
    sc = MinMaxScaler(feature_range = (0, 1))
    inputs = dataset_total.values
    inputs = inputs.reshape(-1, 1)
    sc.fit(inputs)
    inputs = sc.transform(inputs)

    X_test = []
    for i in range(60, len(inputs)): # El bucle termina en la longitud de dataset_total más los datos necesarios
        X_test.append(inputs[i-60:i, 0])

    X_test = np.array(X_test)
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    # Predicción para los datos
    prediccion = model.predict(X_test)
    prediccion = sc.inverse_transform(prediccion)

    # Visualizado de los mismos en el gráfico
    plt.plot(pd.to_datetime(df2.iloc[:, 0]), dataset_total[:].values, color='red', label='real')
    plt.plot(pd.to_datetime(df2.iloc[60:, 0]), prediccion, color='blue', label='predict')

    x = pd.date_range(start=df2.iloc[-1, 0], periods=valoresFuturos+1, freq='200L')[1:]
    plt.plot(x, prediccion[:valoresFuturos], color='green')  

    date_formatter = mdates.DateFormatter('%H:%M:%S')
    ax = plt.gca().xaxis
    ax.set_major_formatter(date_formatter)

    fecha_inicial = df2.iloc[0, 0]
    fecha_final = df2.iloc[-1, 0]
    fecha_inicial = datetime.datetime.strptime(fecha_inicial, '%Y-%m-%dT%H:%M:%S.%f').strftime('%d/%m')
    fecha_final = datetime.datetime.strptime(fecha_final, '%Y-%m-%dT%H:%M:%S.%f').strftime('%d/%m')

    titulo = f'Predicción del estado del vacío {fecha_inicial} - {fecha_final}'

    plt.title(titulo)
    plt.xlabel('Tiempo')
    plt.ylabel('Nivel de vacío')
    plt.legend()
    
    # Guardado del gráfico generado en formato de imagen para su posterior envío por SocketIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()

    # Obtener los datos de la imagen en base64
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    result_queue.put(img_base64)


############################################################################################## 
#                                  RECEPCIÓN DE DATOS                                        #
############################################################################################## 

# Carga del modelo entrenado mediante el programa 'IA'
model = load_model('modelJulen.h5')
contador = 0
contador2 = 0   
data = []
data2 = []

# Función on_message para procesar los mensajes llegados 
def on_message(client, userdata, message):
    global contador, data, contador2, data2
    # Guardado temporal de datos recibidos
    topic = message.topic
    mensaje_recibido = json.loads(message.payload)
    hora = mensaje_recibido["timestamp"]
    valor = mensaje_recibido["value"]
    # Dependiendo desde donde lleguen los mensajes se envían a un sitio y se almacenan en otro
    if topic == "L2_R1":
        socketio.emit('L2_R1', {'hora': hora, 'valor': valor})
        # Si se ha seleccionado en la ventana se guardan los datos en MySQL
        if guardar_pulsado:
            sql = ("INSERT INTO datos (hora, dato, linea, robot, referencia) "
                    "VALUES (%s, %s, %s, %s, %s)")
            valores = (hora, valor, 'Linea 2', 'R1', referencia)
            cursor.execute(sql, valores)
            conexion.commit()
        # Almacenado en una lista para su posterior envío al modelo de predicción
        data.append((hora, float(valor)))
        # Se suma 1 para recopilar los datos necesarios
        contador += 1 
        # Cuando se han recopilado los datos necesarios para predecir los minutos establecidos, se envían a predecir
        if contador == datosparaprediccion: 
            hilo = threading.Thread(target=predecir, args=(data, result_queue1))
            hilo.start()
            graficoPrediccion = result_queue1.get()
            socketio.emit('grafico', graficoPrediccion)
            contador = 0 
            data = []
    elif topic == "L2_R2":
        socketio.emit('L2_R2', {'hora': hora, 'valor': valor})
        if guardar_pulsado:
            sql = "INSERT INTO datos (hora, dato, linea, robot, referencia) VALUES (%s, %s, %s, %s, %s)"
            valores = (hora, valor, 'Linea 2', 'R2', referencia)
            cursor.execute(sql, valores)
            conexion.commit()
        data2.append((hora, float(valor)))
        contador2 += 1 
        if contador2 == datosparaprediccion: 
            hilo = threading.Thread(target=predecir, args=(data2, result_queue2))
            hilo.start()
            graficoPrediccion2 = result_queue2.get()
            socketio.emit('grafico2', graficoPrediccion2)
            contador2 = 0
            data2 = []

    secs = round((datosparaprediccion * 0.2) - (len(data) * 0.2), 1)
    socketio.emit('segundos', {'sec': secs})    


#relacionado con lo del hilo secundario la generacion del plot
plt.ioff()


############################################################################################## 
#                             CONFIG Y RUN DE LA WEB                                         #
############################################################################################## 


# Nueva instancia del cliente MQTT
client = mqtt.Client()

# Dirección IP y el puerto del servidor MQTT en la Raspberry Pi
client.connect("192.168.86.152", 1883, 60)

# Suscripción a cada topic
client.subscribe("L2_R1")
client.subscribe("L2_R2")

client.on_message = on_message

# Función que ejecuta el bucle de publicación/suscripción del cliente MQTT 
def run_mqtt_client():
    client.loop_forever()

# Creacón de hilo para poder ejecutar la web en uno y el bucle del cliente MQTT en otro.
mqtt_thread = threading.Thread(target=run_mqtt_client)
mqtt_thread.start()


# Ruta principal de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

# Inicio de la aplicación Flask mediante SocketIO
if __name__ == '__main__':
    socketio.run(app)
    



    