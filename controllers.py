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
import json
import logging
import os
import traceback

from datetime import datetime, timedelta
from decimal import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from models import User, RoomType, Booking

logger = logging.getLogger(__name__)

if 'logging_level' in os.environ:
    logger.setLevel(os.environ['logging_level'])
else:
    logger.setLevel('INFO')

MA_OTA_PARAM_VERB = 'verb'


class BaseController(object):

    MA_OTA_PARAM_MYA_PROPERTY_ID = 'mya_property_id'
    MA_OTA_PARAM_OTA_PROPERTY_ID = 'ota_property_id'
    MA_OTA_PARAM_SHARED_SECRET = 'shared_secret'

    MA_OTA_SUCCESS = 'success'
    MA_OTA_TYPE = 'type'
    MA_OTA_MSG = 'msg'

    def __init__(self, body):

        self.body = body
        self._errors = []
        self._data = {}
        self._required_params = [
            MA_OTA_PARAM_VERB,
            self.MA_OTA_PARAM_MYA_PROPERTY_ID,
            self.MA_OTA_PARAM_OTA_PROPERTY_ID
        ]

        # Securely removing the shared secret
        shared_secret = self.body.pop(self.MA_OTA_PARAM_SHARED_SECRET, None)

        # Validate the shared secret.
        if shared_secret != os.environ[self.MA_OTA_PARAM_SHARED_SECRET]:
            self._errors.append({
                self.MA_OTA_TYPE: 'api',
                self.MA_OTA_MSG: 'Invalid or missing authentication arguments'
            })

        # Logging the payload before handlers.
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug(json.dumps(self.body))

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def validate(self):
        for param in self._required_params:
            if param not in self.body:
                self._errors.append({
                    self.MA_OTA_TYPE: 'api',
                    self.MA_OTA_MSG: 'Invalid or missing Api arguments'
                })
                logger.error('Request missing a parameter: {0}'.format(param))
                return False
        return True

    def is_error(self):
        return len(self._errors) > 0

    def add_error(self, error_msg):
        self._data[self.MA_OTA_SUCCESS] = False
        self._errors.append({
            self.MA_OTA_TYPE: 'api',
            self.MA_OTA_MSG: error_msg
        })

    def add_required(self, param):
        self._required_params.append(param)

    def perform_action(self):
        pass

    def handle(self):

        with self:
            try:
                self.validate()
                if not self.is_error():
                    self.perform_action()
            except Exception as e:
                self.add_error('Generic error')
                logger.error(traceback.format_exc())

        # Adding the errors to the array
        if self.is_error():
            self._data[self.MA_OTA_SUCCESS] = False
            self._data['errors'] = self._errors
        else:
            self._data[self.MA_OTA_SUCCESS] = True

        # Logging the return payload
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug('Response is: ' + json.dumps(self._data))

        return json.dumps(self._data)


class DatabaseController(BaseController):

    mysql = None

    def __init__(self, body):
        super(DatabaseController, self).__init__(body)
        if DatabaseController.mysql is None:
            DatabaseController.mysql = create_engine('mysql+mysqlconnector://' + os.environ['DB_USER'] + ':' +
                              os.environ['DB_PASS'] + '@' + os.environ['DB_HOST'] + '/' +
                              os.environ['DB_NAME'],
                              echo=(True if 'logging_level' in os.environ and os.environ['logging_level'] == 'DEBUG'
                                    else False),
                              isolation_level='READ COMMITTED', pool_pre_ping=True)
        self.Session = sessionmaker(bind=DatabaseController.mysql)

    def __enter__(self):
        super(DatabaseController, self).__enter__()
        self.session = self.Session()

    def __exit__(self, exc_type, exc_value, traceback):
        super(DatabaseController, self).__exit__(exc_type, exc_value, traceback)
        if self.is_error():
            self.session.rollback()
        else:
            try:
                self.session.commit()
            except DBAPIError as e:
                self.add_error('Generic database error')
                logger.error('MySQL error({0})'.format(e.orig))
            except SQLAlchemyError as e:
                self.add_error('Application specific database error')
                logger.error('SQLAlchemy error({0})'.format(e.code))


class AuthenticatedDatabaseController(DatabaseController):

    def __init__(self, body):
        super(AuthenticatedDatabaseController, self).__init__(body)
        if not self.is_error():
            self.add_required('ota_property_password')

    def perform_action(self):
        super(AuthenticatedDatabaseController, self).perform_action()
        for user in self.session.query(User).filter(User.id == self.body['ota_property_id']):
            if not user.validate_pw(self.body['ota_property_password']):
                self.add_error('Invalid or missing authentication arguments')


class SetupPropertyDatabaseController(AuthenticatedDatabaseController):

    def perform_action(self):
        super(SetupPropertyDatabaseController, self).perform_action()
        if not self.is_error():
            for user in self.session.query(User).filter(User.id == self.body['ota_property_id']):
                user.myallocator_id = self.body['mya_property_id']
                self._data['ota_property_id'] = user.id


class GetRoomTypesDatabaseController(AuthenticatedDatabaseController):

    def perform_action(self):
        super(GetRoomTypesDatabaseController, self).perform_action()
        if not self.is_error():
            self._data['Rooms'] = []
            for room_type in self.session.query(RoomType).join(RoomType.user).\
                    filter(User.id == self.body['ota_property_id']):
                self._data['Rooms'].append({
                    'ota_room_id': room_type.id,
                    'title': room_type.title,
                    'detail': room_type.detail,
                    'occupancy': room_type.occupancy,
                    'dorm': room_type.dorm
                })


class GetBookingListController(AuthenticatedDatabaseController):

    def __init__(self, body):
        super(GetBookingListController, self).__init__(body)
        if not self.is_error():
            self.add_required('ota_booking_version')

    def perform_action(self):
        super(GetBookingListController, self).perform_action()
        if not self.is_error():
            booking_query = self.session.query(Booking).filter(Booking.guid.is_(None)).\
                join(Booking.user).filter(User.id == self.body['ota_property_id'])
            requested_datetime = None if 'ota_booking_version' not in self.body \
                or self.body['ota_booking_version'] is None else \
                datetime.strptime(self.body['ota_booking_version'], '%Y-%m-%d %H:%M:%S')
            if requested_datetime is not None:
                query_datetime = requested_datetime + timedelta(minutes=-5)
                booking_query = booking_query.filter(Booking.dttm >= query_datetime)
            self._data['Bookings'] = []
            for booking in booking_query:
                self._data['Bookings'].append({
                    'booking_id': booking.id,
                    'version': booking.dttm.strftime('%Y-%m-%d %H:%M:%S')
                })


class GetBookingIdController(AuthenticatedDatabaseController):

    def __init__(self, body):
        super(GetBookingIdController, self).__init__(body)
        if not self.is_error():
            self.add_required('booking_id')

    def perform_action(self):
        super(GetBookingIdController, self).perform_action()
        if not self.is_error():
            booking = self.session.query(Booking).get(self.body['booking_id'])
            if 'guid' in self.body:
                booking.guid = self.body['guid']
            self._data['ota_property_id'] = self.body['ota_property_id']
            self._data['mya_property_id'] = self.body['mya_property_id']
            self._data['booking_id'] = self.body['booking_id']
            self._data['Booking'] = {
                'OrderId': self.body['booking_id'],
                'IsCancellation': booking.cancellation,
                'OrderDate': booking.dttm.strftime('%Y-%m-%d'),
                'OrderTime': booking.dttm.strftime('%H:%M:%S'),
                'TotalCurrency': booking.currency,
                'Customers': [],
                'Rooms': []
            }

            # Adding customers from the booking
            for customer in booking.customers:
                self._data['Booking']['Customers'].append({
                    'CustomerCountry': customer.country,
                    'CustomerEmail': customer.email,
                    'CustomerFName': customer.first_name,
                    'CustomerLName': customer.last_name
                })

            # Grouping the booked rooms by type_id
            room_groups = {}
            for booked_room in booking.booked_rooms:
                if booked_room.room_type_id not in room_groups:
                    room_groups[booked_room.room_type_id] = []
                room_groups[booked_room.room_type_id].append(booked_room)

            # Creating the individual room groups
            total_price = Decimal(0.0)
            for room_group_key in room_groups.keys():
                group_dict = {
                    'ChannelRoomType': room_group_key,
                    'Currency': booking.currency,
                    'DayRates': []
                }
                start_date = None
                end_date = None
                group_price = Decimal(0.0)
                for day_rate in room_groups[room_group_key]:
                    if start_date is None or start_date > day_rate.dt:
                        start_date = day_rate.dt
                    if end_date is None or end_date < day_rate.dt:
                        end_date = day_rate.dt
                    group_price = group_price + day_rate.rate
                    group_dict['DayRates'].append({
                        'Date': day_rate.dt.strftime('%Y-%m-%d'),
                        'Description': day_rate.description,
                        'Rate': float(day_rate.rate),
                        'Currency': booking.currency,
                        'RateId': day_rate.rate_id
                    })
                group_dict['EndDate'] = end_date.strftime('%Y-%m-%d')
                group_dict['StartDate'] = start_date.strftime('%Y-%m-%d')
                group_dict['Price'] = float(group_price)
                group_dict['Units'] = 1
                self._data['Booking']['Rooms'].append(group_dict)
                total_price = total_price + group_price
            self._data['Booking']['TotalPrice'] = float(total_price)
