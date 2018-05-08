from flask import Flask

# NOTE: Do not change the order of this code
# The Flask app must be created
# BEFORE you import modules that depend on it !!!

# Create the Flask aoo
app = Flask(__name__)

# Load Configurations
app.config.from_object('config')

app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

import server
import models
import custom_exceptions
