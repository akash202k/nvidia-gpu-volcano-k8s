# model/train.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np

print("Starting training...")

X = np.random.rand(10000, 10)
y = np.random.rand(10000, 1)

model = Sequential([
    Dense(64, activation='relu', input_shape=(10,)),
    Dense(64, activation='relu'),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(X, y, epochs=5, batch_size=64)

print("Training completed.")
