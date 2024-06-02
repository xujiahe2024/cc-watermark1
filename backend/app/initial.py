from flask import Flask
from google.cloud import storage, firestore

def create_app():
    app = Flask(__name__)
    app.config['STORAGE_CLIENT'] = storage.Client()
    app.config['FIRESTORE_CLIENT'] = firestore.Client()
    return app




