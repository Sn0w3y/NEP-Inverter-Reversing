import random

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import numpy as np

def load_data_from_log(file_path):
    byte1, byte2, wattage = [], [], []
    with open(file_path, 'r') as file:
        for line in file.readlines():
            parts = line.strip().split(',')
            if len(parts) == 3:
                b1, b2, w = parts
                byte1.append(int(b1.split(':')[1].strip()))
                byte2.append(int(b2.split(':')[1].strip()))
                wattage.append(int(w.split(':')[1].strip()))
    return np.array(byte1), np.array(byte2), np.array(wattage)

# Load the data
byte1, byte2, wattage = load_data_from_log('log.txt')

# Combine Byte1 and Byte2 into a single feature set and reshape
X = np.vstack([byte1, byte2]).T

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, wattage, test_size=0.2, random_state=42)

# Introduce polynomial features
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly_train = poly.fit_transform(X_train)
X_poly_test = poly.transform(X_test)

# Creating and fitting the model
model = LinearRegression()
model.fit(X_poly_train, y_train)

# Predicting and evaluating the model
y_pred = model.predict(X_poly_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse}")
print(f"R^2 Score: {r2}")

# Model coefficients and intercept
coefs = model.coef_
intercept = model.intercept_
print(f"Model coefficients: {coefs}", f"Model intercept: {intercept}")

# Select random byte1 and byte2 values from the loaded dataset
random_index = random.randint(0, len(byte1) - 1)  # Choose a random index
random_byte1 = byte1[random_index]  # Get the corresponding random byte1 value
random_byte2 = byte2[random_index]  # Get the corresponding random byte2 value

# Example: Predicting wattage with random byte values
new_data = np.array([[random_byte1, random_byte2]])  # Use random byte values
new_data_poly = poly.transform(new_data)  # Transform the new data with polynomial features
predicted_wattage = model.predict(new_data_poly)  # Predict the wattage

print(f"Randomly selected Byte1: {random_byte1}, Byte2: {random_byte2}")
print(f"Predicted wattage for [Byte1: {random_byte1}, Byte2: {random_byte2}]: {predicted_wattage[0]}")
