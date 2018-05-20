#
# Copyright 2018 Stephen Cuppett
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest
import index
import uuid

from controllers import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User

SHARED_SECRET = 'test123'

os.environ['shared_secret'] = SHARED_SECRET
os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = ''
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'test'

mysql = create_engine('mysql+mysqlconnector://' + os.environ['DB_USER'] + ':' +
                      os.environ['DB_PASS'] + '@' + os.environ['DB_HOST'] + '/' +
                      os.environ['DB_NAME'], isolation_level='READ COMMITTED',
                      pool_pre_ping=True)
Session = sessionmaker(bind=mysql)


class TestGetRoomTypes(unittest.TestCase):

    def test_get_room_types_happy_path(self):

        # Building a new property to store
        password = 'supersecretpassword'
        email = str(uuid.uuid4()) + '@example.com'
        new_user = User(password=password, id=email)

        # Storing the initial property for this test
        session = Session()
        session.add(new_user)
        session.commit()

        # Storing a few new room types for this test
        count = 1
        while count < 4:
            new_room_type = RoomType(id=str(uuid.uuid4()), user_id=email, title='Title ' + str(count),
                                     detail='Detail ' + str(count), dorm=False, occupancy=count)
            session.add(new_room_type)
            count = count + 1
        session.commit()

        # Run the transaction
        event = {
            "verb": "GetRoomTypes",
            "mya_property_id": "Test1MyaPropertyID",
            "ota_property_id": email,
            "ota_property_password": password,
            "shared_secret": SHARED_SECRET
        }

        result = index.router(event, None)

        # Validate the API call
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        body = json.loads(result['body'])
        print(result['body'])
        self.assertFalse('errors' in body)
        self.assertEqual(body['success'], True)
        self.assertEqual(len(body['Rooms']), 3)


if __name__ == '__main__':
    unittest.main()
