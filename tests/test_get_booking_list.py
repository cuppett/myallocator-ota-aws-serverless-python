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
from models import Customer

SHARED_SECRET = 'test123'

os.environ['shared_secret'] = SHARED_SECRET
os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = ''
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'test'

mysql = create_engine('mysql+mysqlconnector://' + os.environ['DB_USER'] + ':' +
                      os.environ['DB_PASS'] + '@' + os.environ['DB_HOST'] + '/' +
                      os.environ['DB_NAME'], echo=True, isolation_level='READ COMMITTED',
                      pool_pre_ping=True)
Session = sessionmaker(bind=mysql)


class TestGetBookingList(unittest.TestCase):

    def test_get_list_happy_path(self):

        # Building a new property to store
        password = 'supersecretpassword'
        email = str(uuid.uuid4()) + '@gmail.com'
        new_user = User(password=password, id=email)

        # Storing the initial property for this test
        session = Session()
        try:
            session.add(new_user)
            session.commit()
        except:
            session.rollback()

        new_customer = Customer(email=email, first_name='John', last_name='Doe')
        session.add(new_customer)
        session.commit()

        # Storing a few new bookings for this test
        count = 1
        try:
            while count < 4:
                dttm = datetime.now() + timedelta(hours=(-1 * count))
                new_booking = Booking(id=str(uuid.uuid4()), user_id=new_user.id, dttm=dttm)
                new_booking.customers.append(new_customer)
                session.add(new_booking)
                count = count + 1
            session.commit()
        except:
            print(traceback.format_exc())
            session.rollback()

        # Run the transaction
        event = {
            'verb': 'GetBookingList',
            'mya_property_id': 'Test1MyaPropertyID',
            'ota_property_id': email,
            'ota_booking_version': (datetime.now() + timedelta(hours=-2)).strftime('%Y-%m-%d %H:%M:%S'),
            "ota_property_password": password,
            'shared_secret': SHARED_SECRET
        }
        result = index.router(event, None)

        # Validate the API call
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        body = json.loads(result['body'])
        self.assertFalse('errors' in body)
        self.assertEqual(body['success'], True)
        self.assertEqual(len(body['Bookings']), 2)

    def test_get_list_null_no_listings(self):

        # Building a new property to store
        password = 'supersecretpassword'
        email = str(uuid.uuid4()) + '@gmail.com'
        new_user = User(password=password, id=email)

        # Storing the initial property for this test
        session = Session()
        try:
            session.add(new_user)
            session.commit()
        except:
            session.rollback()

        # Run the transaction
        event = {
            'verb': 'GetBookingList',
            'mya_property_id': 'Test1MyaPropertyID',
            'ota_property_id': email,
            'ota_booking_version': None,
            "ota_property_password": password,
            'shared_secret': SHARED_SECRET
        }
        result = index.router(event, None)

        # Validate the API call
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        body = json.loads(result['body'])
        self.assertFalse('errors' in body)
        self.assertEqual(body['success'], True)
        self.assertEqual(len(body['Bookings']), 0)


if __name__ == '__main__':
    unittest.main()
