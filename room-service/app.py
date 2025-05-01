import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pykafka import KafkaClient
import logging
import threading
import time
from sqlalchemy import create_engine

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:123@postgres:5432/rooms_db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure database exists
try:
    engine = create_engine(database_url.replace('rooms_db', 'postgres'))
    conn = engine.connect()
    conn.execute("CREATE DATABASE IF NOT EXISTS rooms_db")
    conn.close()
except Exception as e:
    logging.error(f"Database creation failed: {e}")

# Kafka setup
kafka_host = os.environ.get('KAFKA_HOST', 'kafka:9092')
try:
    client = KafkaClient(hosts=kafka_host)
    rooms_topic = client.topics['rooms']
    users_topic = client.topics['users']
    reservations_topic = client.topics['reservations']
    rooms_producer = rooms_topic.get_sync_producer()
    users_consumer = users_topic.get_simple_consumer()
    reservations_consumer = reservations_topic.get_simple_consumer()
except Exception as e:
    logging.error(f"Kafka connection failed: {e}")
    rooms_producer = users_consumer = reservations_consumer = None

# Database model
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    available = db.Column(db.Boolean, default=True)

# Background thread for consuming Kafka messages
def consume_kafka():
    while True:
        if users_consumer:
            for msg in users_consumer:
                if msg is not None:
                    logging.info(f"Users topic: {msg.value.decode('utf-8')}")
        if reservations_consumer:
            for msg in reservations_consumer:
                if msg is not None:
                    logging.info(f"Reservations topic: {msg.value.decode('utf-8')}")
        time.sleep(0.1)

threading.Thread(target=consume_kafka, daemon=True).start()

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{"id": r.id, "name": r.name, "available": r.available} for r in rooms])

@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    room = Room(name=data['name'], available=True)
    db.session.add(room)
    db.session.commit()
    if rooms_producer:
        rooms_producer.produce(f"Room {room.name} created".encode('utf-8'))
    return jsonify({"id": room.id, "name": room.name, "available": room.available}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
