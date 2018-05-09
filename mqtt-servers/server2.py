"""

A small Test application to show how to use Flask-MQTT.

"""

import eventlet
import json
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    #mqtt.publish(data['topic'], data['message'])

@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    #mqtt.subscribe(data['topic'])

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    print('Server 2: Received message', data['payload'], 'from topic: ', data['topic'])
    socketio.emit('mqtt_message', data=data)

@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)

if __name__ == '__main__':
    #print('Server 2: subscribing to rmpbpp')
    #socketio.emit('subscribe', None)
    mqtt.subscribe('channel01')
    socketio.run(app, host='0.0.0.0', port=5001, use_reloader=True, debug=True)
