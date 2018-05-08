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
Item Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
"""

import unittest
import os
import json
from mock import patch
from redis import Redis, ConnectionError
from werkzeug.exceptions import NotFound
from app.models import Item
from app.custom_exceptions import DataValidationError
from app import server  # to get Redis

VCAP_SERVICES = os.getenv('VCAP_SERVICES', None)
if not VCAP_SERVICES:
    VCAP_SERVICES = '{"rediscloud": [{"credentials": {' \
        '"password": "", "hostname": "127.0.0.1", "port": "6379"}}]}'


######################################################################
#  T E S T   C A S E S
######################################################################
class TestItems(unittest.TestCase):
    """ Test Cases for Item Model """

    def setUp(self):
        """ Initialize the Redis database """
        Item.init_db()
        Item.remove_all()

    def test_create_a_item(self):
        """ Create a item and assert that it exists """
        item = Item(0, "fido", "dog", False)
        self.assertNotEqual(item, None)
        self.assertEqual(item.id, 0)
        self.assertEqual(item.name, "fido")
        self.assertEqual(item.price, "dog")
        self.assertEqual(item.available, False)

    def test_add_a_item(self):
        """ Create a item and add it to the database """
        items = Item.all()
        self.assertEqual(items, [])
        item = Item(0, "fido", "dog", True)
        self.assertTrue(item != None)
        self.assertEqual(item.id, 0)
        item.save()
        # Asert that it was assigned an id and shows up in the database
        self.assertEqual(item.id, 1)
        items = Item.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, 1)
        self.assertEqual(items[0].name, "fido")
        self.assertEqual(items[0].price, "dog")
        self.assertEqual(items[0].available, True)

    def test_update_a_item(self):
        """ Update a Item """
        item = Item(0, "fido", "dog", True)
        item.save()
        self.assertEqual(item.id, 1)
        # Change it an save it
        item.price = "k9"
        item.save()
        self.assertEqual(item.id, 1)
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        items = Item.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].price, "k9")
        self.assertEqual(items[0].name, "fido")

    def test_delete_a_item(self):
        """ Delete a Item """
        item = Item(0, "fido", "dog")
        item.save()
        self.assertEqual(len(Item.all()), 1)
        # delete the item and make sure it isn't in the database
        item.delete()
        self.assertEqual(len(Item.all()), 0)

    def test_serialize_a_item(self):
        """ Serialize a Item """
        item = Item(0, "fido", "dog")
        data = item.serialize()
        self.assertNotEqual(data, None)
        self.assertIn('id', data)
        self.assertEqual(data['id'], 0)
        self.assertIn('name', data)
        self.assertEqual(data['name'], "fido")
        self.assertIn('price', data)
        self.assertEqual(data['price'], "dog")

    def test_deserialize_a_item(self):
        """ Deserialize a Item """
        data = {"id":1, "name": "kitty", "price": "cat", "available": True}
        item = Item(data['id'])
        item.deserialize(data)
        self.assertNotEqual(item, None)
        self.assertEqual(item.id, 1)
        self.assertEqual(item.name, "kitty")
        self.assertEqual(item.price, "cat")

    def test_deserialize_with_no_name(self):
        """ Deserialize a Item that has no name """
        data = {"id":0, "price": "cat"}
        item = Item(0)
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_with_no_data(self):
        """ Deserialize a Item that has no data """
        item = Item(0)
        self.assertRaises(DataValidationError, item.deserialize, None)

    def test_deserialize_with_bad_data(self):
        """ Deserialize a Item that has bad data """
        item = Item(0)
        self.assertRaises(DataValidationError, item.deserialize, "string data")

    def test_save_a_item_with_no_name(self):
        """ Save a Item with no name """
        item = Item(0, None, "cat")
        self.assertRaises(DataValidationError, item.save)

    def test_find_item(self):
        """ Find a Item by id """
        Item(0, "fido", "dog").save()
        Item(0, "kitty", "cat").save()
        item = Item.find(2)
        self.assertIsNot(item, None)
        self.assertEqual(item.id, 2)
        self.assertEqual(item.name, "kitty")

    def test_find_with_no_items(self):
        """ Find a Item with empty database """
        item = Item.find(1)
        self.assertIs(item, None)

    def test_item_not_found(self):
        """ Find a Item that doesnt exist """
        Item(0, "fido", "dog").save()
        item = Item.find(2)
        self.assertIs(item, None)

    def test_find_by_name(self):
        """ Find a Item by Name """
        Item(0, "fido", "dog").save()
        Item(0, "kitty", "cat").save()
        items = Item.find_by_name("fido")
        self.assertNotEqual(len(items), 0)
        self.assertEqual(items[0].price, "dog")
        self.assertEqual(items[0].name, "fido")

    def test_find_by_price(self):
        """ Find a Item by Price """
        Item(0, "fido", "dog").save()
        Item(0, "kitty", "cat").save()
        items = Item.find_by_price("cat")
        self.assertNotEqual(len(items), 0)
        self.assertEqual(items[0].price, "cat")
        self.assertEqual(items[0].name, "kitty")

    def test_find_by_availability(self):
        """ Find a Item by Availability """
        Item(0, "fido", "dog", False).save()
        Item(0, "kitty", "cat", True).save()
        items = Item.find_by_availability(True)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "kitty")

    def test_for_case_insensitive(self):
        """ Test for Case Insensitive Search """
        Item(0, "Fido", "DOG").save()
        Item(0, "Kitty", "CAT").save()
        items = Item.find_by_name("fido")
        self.assertNotEqual(len(items), 0)
        self.assertEqual(items[0].name, "Fido")
        items = Item.find_by_price("cat")
        self.assertNotEqual(len(items), 0)
        self.assertEqual(items[0].price, "CAT")

#    @patch.dict(os.environ, {'VCAP_SERVICES': json.dumps(VCAP_SERVICES).encode('utf8')})
    @patch.dict(os.environ, {'VCAP_SERVICES': VCAP_SERVICES})
    def test_vcap_services(self):
        """ Test if VCAP_SERVICES works """
        Item.init_db()
        self.assertIsNotNone(Item.redis)

    @patch('redis.Redis.ping')
    def test_redis_connection_error(self, ping_error_mock):
        """ Test a Bad Redis connection """
        ping_error_mock.side_effect = ConnectionError()
        self.assertRaises(ConnectionError, Item.init_db)
        self.assertIsNone(Item.redis)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestItems)
    # unittest.TextTestRunner(verbosity=2).run(suite)
