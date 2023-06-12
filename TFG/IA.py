import pandas as pd
from keras.models import Sequential
from keras.layers import *
from keras.callbacks import *
from keras.losses import *
from keras.metrics import *
from keras.optimizers import *
from keras.models import *
import matplotlib.pyplot as plt


###########################################################################
#                      Transformación inicial de fd                       #
###########################################################################

df = pd.read_csv('datoos2.csv', sep=';')

df['linea'] = df['linea'].str.replace('Linea 2', '2')
df['linea'] = df['linea'].astype(int)

df['robot'] = df['robot'].str.replace('R1', '1')
df['robot'] = df['robot'].str.replace('R2', '2')
df['robot'] = df['robot'].astype(int)

df['referencia'] = df['referencia'].str.replace('programa1', '1')
df['referencia'] = df['referencia'].str.replace('programa2', '2')
df['referencia'] = df['referencia'].str.replace('programa3', '3')
df['referencia'] = df['referencia'].str.replace('programa4', '4')
df['referencia'] = df['referencia'].astype(int)

df['hora'] = pd.to_datetime(df['hora'], format='%Y-%m-%d %H:%M:%S.%f')
df['dato'] = df['dato'].astype(float)



###########################################################################
#                        Separación de los datos                         #
###########################################################################

import numpy as np
n = int(len(df) * 0.85) 
training_set = df.iloc[:n, 1:2].values 
test_set = df.iloc[n:, 1:2].values 

from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range = (0, 1))
training_set_scaled = sc.fit_transform(training_set)

# Creating a data structure with 60 time-steps and 1 output
X_train = []
y_train = []
for i in range(60, n):
    X_train.append(training_set_scaled[i-60:i, 0])
    y_train.append(training_set_scaled[i, 0])
X_train, y_train = np.array(X_train), np.array(y_train)
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
'''

###########################################################################
#                        Entrenamiento del modelo                         #
###########################################################################

model = Sequential()

model.add(LSTM(units = 50, return_sequences = True, input_shape = (X_train.shape[1], 1)))
model.add(Dropout(0.2))
# Adding a second LSTM layer and some Dropout regularisation
model.add(LSTM(units = 50, return_sequences = True))
model.add(Dropout(0.2))
# Adding a third LSTM layer and some Dropout regularisation
model.add(LSTM(units = 50, return_sequences = True))
model.add(Dropout(0.2))
# Adding a fourth LSTM layer and some Dropout regularisation
model.add(LSTM(units = 50))
model.add(Dropout(0.2))
# Adding the output layer
model.add(Dense(units = 1))

# Compiling the RNN
model.compile(optimizer = 'adam', loss = 'mean_squared_error')
# Fitting the RNN to the Training set
model.fit(X_train, y_train, epochs = 30, batch_size = 32)
model.save('modelJulen.h5')

###########################################################################
#                    PREDICCION COMPLETO - ACUAL + FUTURA                 #
###########################################################################
'''
model = load_model('modelJulen.h5')
dataset_train = df.iloc[:n, 1:2] # Coge las primeras n filas de la columna "open"
dataset_test = df.iloc[n:, 1:2] # Coge las filas restantes de la columna "open"
dataset_total = pd.concat((dataset_train, dataset_test), axis = 0)

ValoresFuturos = 0

inputs = dataset_total[len(dataset_total) - len(dataset_test) - (60+ValoresFuturos):].values # Coge los últimos x valores del dataset_train y todos los del dataset_test
inputs = inputs.reshape(-1,1)
inputs = sc.transform(inputs)

X_test = []
for i in range(60, len(inputs)): # El bucle termina en la longitud de dataset_test más 60 + valores a predecir
    X_test.append(inputs[i-60:i, 0])

X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

prediccion = model.predict(X_test)
prediccion = sc.inverse_transform(prediccion)


###########################################################################
#                         Visualizado de datos                           #
###########################################################################

plt.plot(pd.to_datetime(df.iloc[n:, 0]), dataset_test.values, color='red', label='real')
plt.plot(pd.to_datetime(df.iloc[n:, 0]), prediccion[:len(dataset_test)], color='blue', label='predict')
    
# Crea un nuevo eje x para los 100 valores restantes de predicted_stock_price
x = pd.date_range(start=df.iloc[-1, 0], periods=ValoresFuturos+1, freq='S')[1:]

# Traza los x valores restantes de predicted_stock_price en el mismo gráfico
plt.plot(x, prediccion[len(dataset_test):], color='blue')

plt.title('Prediccion del estado del vacío')
plt.xlabel('Tiempo')
plt.ylabel('Nivel de vacío')
plt.legend()
plt.show()

