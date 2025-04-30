from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pykafka import KafkaClient
import logging
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/reservations_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Kafka setup
try:
    client = KafkaClient(hosts="localhost:9092")
    reservations_topic = client.topics['reservations']
    users_topic = client.topics['users']
    rooms_topic = client.topics['rooms']
    reservations_producer = reservations_topic.get_sync_producer()
    users_consumer = users_topic.get_simple_consumer()
    rooms_consumer = rooms_topic.get_simple_consumer()
except Exception as e:
    logging.error(f"Kafka connection failed: {e}")
    reservations_producer = users_consumer = rooms_consumer = None

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

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
        time.sleep(0.1)

threading.Thread(target=consume_kafka, daemon=True).start()

@app.route('/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([{"id": r.id, "user_id": r.user_id, "room_id": r.room_id} for r in reservations])

@app.route('/reservations', methods=['POST'])
def create_reservation():
    data = request.get_json()
    reservation = Reservation(user_id=data['user_id'], room_id=data['room_id'])
    db.session.add(reservation)
    db.session.commit()
    if reservations_producer:
        reservations_producer.produce(f"Reservation for room {data['room_id']}".encode('utf-8'))
    return jsonify({"id": reservation.id, "user_id": reservation.user_id, "room_id": reservation.room_id}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
