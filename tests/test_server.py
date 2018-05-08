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

"""
Item API Service Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
"""

import unittest
import logging
import json
from app import server

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409

######################################################################
#  T E S T   C A S E S
######################################################################
class TestItemServer(unittest.TestCase):
    """ Item Service tests """

    def setUp(self):
        self.app = server.app.test_client()
        server.initialize_logging(logging.CRITICAL)
        server.init_db()
        server.data_reset()
        server.data_load({"name": "fido", "price": "dog", "available": True})
        server.data_load({"name": "kitty", "price": "cat", "available": True})

    def test_index(self):
        """ Test the index page """
        resp = self.app.get('/')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertIn('Item Demo REST API Service', resp.data)

    def test_get_item_list(self):
        """ Get a list of Items """
        resp = self.app.get('/items')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)

    def test_get_item(self):
        """ get a single Item """
        resp = self.app.get('/items/2')
        #print 'resp_data: ' + resp.data
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = json.loads(resp.data)
        self.assertEqual(data['name'], 'kitty')

    def test_get_item_not_found(self):
        """ Get a Item that doesn't exist """
        resp = self.app.get('/items/0')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)
        data = json.loads(resp.data)
        self.assertIn('was not found', data['message'])

    def test_create_item(self):
        """ Create a new Item """
        # save the current number of items for later comparrison
        item_count = self.get_item_count()
        # add a new item
        new_item = {'name': 'sammy', 'price': 'snake', 'available': True}
        data = json.dumps(new_item)
        resp = self.app.post('/items', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get('Location', None)
        self.assertNotEqual(location, None)
        # Check the data is correct
        new_json = json.loads(resp.data)
        self.assertEqual(new_json['name'], 'sammy')
        # check that count has gone up and includes sammy
        resp = self.app.get('/items')
        # print 'resp_data(2): ' + resp.data
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(len(data), item_count + 1)
        self.assertIn(new_json, data)

    def test_update_item(self):
        """ Update a Item """
        new_kitty = {'name': 'kitty', 'price': 'tabby', 'available': True}
        data = json.dumps(new_kitty)
        resp = self.app.put('/items/2', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.get('/items/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        new_json = json.loads(resp.data)
        self.assertEqual(new_json['price'], 'tabby')

    def test_update_item_with_no_name(self):
        """ Update a Item without assigning a name """
        new_item = {'price': 'dog'}
        data = json.dumps(new_item)
        resp = self.app.put('/items/2', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_update_item_not_found(self):
        """ Update a Item that doesn't exist """
        new_kitty = {"name": "timothy", "price": "mouse"}
        data = json.dumps(new_kitty)
        resp = self.app.put('/items/0', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_delete_item(self):
        """ Delete a Item """
        # save the current number of items for later comparrison
        item_count = self.get_item_count()
        # delete a item
        resp = self.app.delete('/items/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        new_count = self.get_item_count()
        self.assertEqual(new_count, item_count - 1)

    def test_create_item_with_no_name(self):
        """ Create a Item without a name """
        new_item = {'price': 'dog'}
        data = json.dumps(new_item)
        resp = self.app.post('/items', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_create_item_no_content_type(self):
        """ Create a Item with no Content-Type """
        new_item = {'price': 'dog'}
        data = json.dumps(new_item)
        resp = self.app.post('/items', data=data)
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_get_nonexisting_item(self):
        """ Get a nonexisting Item """
        resp = self.app.get('/items/5')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_call_create_with_an_id(self):
        """ Call create passing anid """
        new_item = {'name': 'sammy', 'price': 'snake'}
        data = json.dumps(new_item)
        resp = self.app.post('/items/1', data=data)
        self.assertEqual(resp.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_query_item_list(self):
        """ Query Items by price """
        resp = self.app.get('/items', query_string='price=dog')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        self.assertIn('fido', resp.data)
        self.assertNotIn('kitty', resp.data)
        data = json.loads(resp.data)
        query_item = data[0]
        self.assertEqual(query_item['price'], 'dog')

    def test_purchase_a_item(self):
        """ Purchase a Item """
        resp = self.app.put('/items/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.get('/items/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        item_data = json.loads(resp.data)
        self.assertEqual(item_data['available'], False)

    def test_purchase_not_available(self):
        """ Purchase a Item that is not available """
        resp = self.app.put('/items/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.put('/items/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)
        resp_json = json.loads(resp.get_data())
        self.assertIn('not available', resp_json['message'])


######################################################################
# Utility functions
######################################################################

    def get_item_count(self):
        """ save the current number of items """
        resp = self.app.get('/items')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = json.loads(resp.data)
        return len(data)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
