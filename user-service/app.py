import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pykafka import KafkaClient
import logging
import threading
import time
from sqlalchemy import create_engine

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:123@postgres:5432/users_db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure database exists
try:
    engine = create_engine(database_url.replace('users_db', 'postgres'))
    conn = engine.connect()
    conn.execute("CREATE DATABASE IF NOT EXISTS users_db")
    conn.close()
except Exception as e:
    logging.error(f"Database creation failed: {e}")

# Kafka setup
kafka_host = os.environ.get('KAFKA_HOST', 'kafka:9092')
try:
    client = KafkaClient(hosts=kafka_host)
    users_topic = client.topics['users']
    rooms_topic = client.topics['rooms']
    reservations_topic = client.topics['reservations']
    users_producer = users_topic.get_sync_producer()
    users_consumer = users_topic.get_simple_consumer()
    rooms_consumer = rooms_topic.get_simple_consumer()
    reservations_consumer = reservations_topic.get_simple_consumer()
except Exception as e:
    logging.error(f"Kafka connection failed: {e}")
    users_producer = users_consumer = rooms_consumer = reservations_consumer = None

# Database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), default='Employee')  # Employee, Admin, Visitor

# Background thread for consuming Kafka messages
def consume_kafka():
    while True:
        if users_consumer:
            for msg in users_consumer:
                if msg is not None:
                    logging.info(f"Users topic: {msg.value.decode('utf-8')}")
        if rooms_consumer:
            for msg in rooms_consumer:
                if msg is not None:
                    logging.info(f"Rooms topic: {msg.value.decode('utf-8')}")
        if reservations_consumer:
            for msg in reservations_consumer:
                if msg is not None:
                    logging.info(f"Reservations topic: {msg.value.decode('utf-8')}")
        time.sleep(0.1)

threading.Thread(target=consume_kafka, daemon=True).start()

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "role": u.role} for u in users])

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    if users_producer:
        users_producer.produce(f"User {user.name} accessed".encode('utf-8'))
    return jsonify({"id": user.id, "name": user.name, "role": user.role})

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(name=data['name'], role=data.get('role', 'Employee'))
    db.session.add(user)
    db.session.commit()
    if users_producer and user.role == 'Admin':
        users_producer.produce(f"User {user.name} assigned Admin role".encode('utf-8'))
    return jsonify({"id": user.id, "name": user.name, "role": user.role}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
