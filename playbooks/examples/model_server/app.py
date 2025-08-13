from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.get("/predict")
def predict():
    return jsonify({"prediction": random.random()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


