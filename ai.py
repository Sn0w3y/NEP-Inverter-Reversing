import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Configuration
LOG_FILE = 'log.txt'
MODEL_FILE = 'model.joblib'
POLYNOMIAL_DEGREE = 2
ACCURACY_THRESHOLD = 0.96
RECHECK_INTERVAL = 10  # Time in seconds to wait between checks when the file is not modified.


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


def train_and_evaluate(X, y, degree):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    mse = mean_squared_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred)

    print(f'Mean Squared Error: {mse}')
    print(f'R^2 Score: {r2}')

    return model, mse, r2


def check_and_retrain():
    byte1, byte2, wattage = load_data_from_log(LOG_FILE)

    # Combine byte1 and byte2 into a single numpy array X
    X = np.hstack([byte1.reshape(-1, 1), byte2.reshape(-1, 1)])
    y = wattage

    try:
        model = joblib.load(MODEL_FILE)
        print("Model loaded.")
    except FileNotFoundError:
        print("Model file not found. Training a new model.")
        model, mse, r2 = train_and_evaluate(X, y, POLYNOMIAL_DEGREE)
        joblib.dump(model, MODEL_FILE)
        return

    # Evaluate current model with new data
    _, _, r2 = train_and_evaluate(X, y, POLYNOMIAL_DEGREE)
    if r2 < ACCURACY_THRESHOLD:
        print("Retraining model due to performance below threshold.")
        model, mse, r2 = train_and_evaluate(X, y, POLYNOMIAL_DEGREE)
        joblib.dump(model, MODEL_FILE)
    else:
        print("Current model meets performance threshold.")


class DatasetChangeHandler(FileSystemEventHandler):
    """Handles changes in the dataset file."""

    def on_modified(self, event):
        if event.src_path.endswith(LOG_FILE):
            print(f"{LOG_FILE} has been modified. Checking and potentially retraining model.")
            check_and_retrain()


def main():
    event_handler = DatasetChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(RECHECK_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
