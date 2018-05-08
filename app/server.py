######################################################################
# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Item Store Service with UI

Paths:
------
GET / - Displays a UI for Selenium testing
GET /items - Returns a list all of the Items
GET /items/{id} - Returns the Item with a given id number
POST /items - creates a new Item record in the database
PUT /items/{id} - updates a Item record in the database
DELETE /items/{id} - deletes a Item record in the database
"""

import sys
import logging
from flask import jsonify, request, json, url_for, make_response, abort
from flask_api import status    # HTTP Status Codes
from werkzeug.exceptions import NotFound
from app.models import Item
from . import app

import eventlet
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

eventlet.monkey_patch()

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)
count = 0

topic = 'channel01'
message = ''

# Error handlers reuire app to be initialized so we must import
# then only after we have initialized the Flask app instance
import error_handlers

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route('/healthcheck')
def healthcheck():
    """ Let them know our heart is still beating """
    return make_response(jsonify(status=200, message='Healthy'), status.HTTP_200_OK)

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    # data = '{name: <string>, price: <string>}'
    # url = request.base_url + 'items' # url_for('list_items')
    # return jsonify(name='Item Demo REST API Service', version='1.0', url=url, data=data), status.HTTP_200_OK
    return app.send_static_file('index.html')

######################################################################
# LIST ALL PETS
######################################################################
@app.route('/items', methods=['GET'])
def list_items():
    """ Returns all of the Items """
    items = []
    price = request.args.get('price')
    name = request.args.get('name')
    if price:
        items = Item.find_by_price(price)
    elif name:
        items = Item.find_by_name(name)
    else:
        items = Item.all()

    results = [item.serialize() for item in items]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PET
######################################################################
@app.route('/items/<int:item_id>', methods=['GET'])
def get_items(item_id):
    """
    Retrieve a single Item

    This endpoint will return a Item based on it's id
    """
    item = Item.find(item_id)
    if not item:
        raise NotFound("Item with id '{}' was not found.".format(item_id))
    return make_response(jsonify(item.serialize()), status.HTTP_200_OK)

######################################################################
# ADD A NEW PET
######################################################################
@app.route('/items', methods=['POST'])
def create_items():
    """
    Creates a Item
    This endpoint will create a Item based the data in the body that is posted
    """
    data = {}
    # Check for form submission data
    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        app.logger.info('Getting data from form submit')
        data = {
            'name': request.form['name'],
            'price': request.form['price'],
            'available': True
        }
    else:
        app.logger.info('Getting data from API call')
        data = request.get_json()
    app.logger.info(data)
    item = Item()
    item.deserialize(data)
    item.save()
    message = item.serialize()
    location_url = url_for('get_items', item_id=item.id, _external=True)
    return make_response(jsonify(message), status.HTTP_201_CREATED,
                         {'Location': location_url})


######################################################################
# UPDATE AN EXISTING PET
######################################################################
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_items(item_id):
    """
    Update a Item

    This endpoint will update a Item based the body that is posted
    """
    check_content_type('application/json')
    item = Item.find(item_id)
    if not item:
        raise NotFound("Item with id '{}' was not found.".format(item_id))
    data = request.get_json()
    app.logger.info(data)
    item.deserialize(data)
    item.id = item_id
    item.save()
    mqtt_update_message = "Price of the Item with id '{}' and name '{}' was changed.".format(item_id, item.name)
    mqtt.publish(topic, mqtt_update_message)
    return make_response(jsonify(item.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE A PET
######################################################################
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_items(item_id):
    """
    Delete a Item

    This endpoint will delete a Item based the id specified in the path
    """
    item = Item.find(item_id)
    if item:
        item.delete()
    return make_response('', status.HTTP_204_NO_CONTENT)

######################################################################
# PURCHASE A PET
######################################################################
@app.route('/items/<int:item_id>/purchase', methods=['PUT'])
def purchase_items(item_id):
    """ Purchasing a Item makes it unavailable """
    item = Item.find(item_id)
    if not item:
        abort(status.HTTP_404_NOT_FOUND, "Item with id '{}' was not found.".format(item_id))
    if not item.available:
        abort(status.HTTP_400_BAD_REQUEST, "Item with id '{}' is not available.".format(item_id))
    item.available = False
    item.save()
    return make_response(jsonify(item.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE ALL PET DATA (for testing only)
######################################################################
@app.route('/items/reset', methods=['DELETE'])
def items_reset():
    """ Removes all items from the database """
    Item.remove_all()
    return make_response('', status.HTTP_204_NO_CONTENT)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

@app.before_first_request
def init_db(redis=None):
    """ Initlaize the model """
    Item.init_db(redis)

# load sample data
def data_load(payload):
    """ Loads a Item into the database """
    item = Item(0, payload['name'], payload['price'])
    item.save()

def data_reset():
    """ Removes all Items from the database """
    Item.remove_all()

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers['Content-Type'] == content_type:
        return
    app.logger.error('Invalid Content-Type: %s', request.headers['Content-Type'])
    abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 'Content-Type must be {}'.format(content_type))

#@app.before_first_request
def initialize_logging(log_level=logging.INFO):
    """ Initialized the default logging to STDOUT """
    if not app.debug:
        print 'Setting up logging...'
        # Set up default logging for submodules to use STDOUT
        # datefmt='%m/%d/%Y %I:%M:%S %p'
        fmt = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        logging.basicConfig(stream=sys.stdout, level=log_level, format=fmt)
        # Make a new log handler that uses STDOUT
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(log_level)
        # Remove the Flask default handlers and use our own
        handler_list = list(app.logger.handlers)
        for log_handler in handler_list:
            app.logger.removeHandler(log_handler)
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        app.logger.info('Logging handler established')

@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(topic, message)

@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    mqtt.subscribe(topic)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    #print('Server 1 handle_mqtt_message: Received message', data['payload'], 'from topic: ', data['topic'])
    #mqtt.unsubscribe('rmpbpp')
    #print('Server 1: unsubscribed!')
    socketio.emit('mqtt_message', data=data)

@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)
