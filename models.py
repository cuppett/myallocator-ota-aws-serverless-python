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
from bcrypt import gensalt, hashpw, checkpw
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):

    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    myallocator_id = Column(String)
    __password = Column('password', String, nullable=False)
    room_types = relationship("RoomType", back_populates="user")
    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return "<User(id='%s')>" % self.id

    def validate_pw(self, password):
        return checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        salt = gensalt()
        self.__password = hashpw(value.encode('utf-8'), salt).decode()


class RoomType(Base):
    __tablename__ = 'room_types'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    title = Column(String)
    detail = Column(String)
    occupancy = Column(Integer, nullable=False)
    dorm = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="room_types")
    booked_rooms = relationship("BookingRoom", back_populates="room_type")

    def __repr__(self):
        return "<RoomType(id='%s')>" % self.id


booking_customers = Table('booking_customers', Base.metadata,
    Column('booking_id', String, ForeignKey('bookings.id')),
    Column('email', String, ForeignKey('customers.email'))
)


class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(String, primary_key=True, nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    dttm = Column(DateTime, nullable=False)
    currency = Column(String, default='USD')
    cancellation = Column(Boolean, nullable=False, default=False)
    guid = Column('myallocator_guid', String)

    user = relationship("User", back_populates="bookings")
    booked_rooms = relationship("BookingRoom", back_populates="booking")
    customers = relationship("Customer", secondary=booking_customers, back_populates="bookings")

    def __repr__(self):
        return "<Booking(id='%s')>" % self.id


class Customer(Base):
    __tablename__ = 'customers'
    email = Column(String, primary_key=True)
    country = Column(String, nullable=False, default='US')
    first_name = Column(String)
    last_name = Column(String)

    bookings = relationship("Booking", secondary=booking_customers, back_populates="customers")

    def __repr__(self):
        return "<Customer(id='%s')>" % self.email


class BookingRoom(Base):
    __tablename__ = 'booking_rooms'
    booking_id = Column(String, ForeignKey('bookings.id'), nullable=False, primary_key=True)
    room_type_id = Column(String, ForeignKey('room_types.id'), nullable=False, primary_key=True)
    dt = Column(Date, nullable=False, primary_key=True)
    description = Column(String)
    rate = Column(Numeric, nullable=False)
    rate_id = Column(String)

    booking = relationship("Booking", back_populates="booked_rooms")
    room_type = relationship("RoomType", back_populates="booked_rooms")

    def __repr__(self):
        return "<BookingRoom(booking_id='%s' room_id='%s', date='%s')>" % self.booking_id, self.room_type_id, str(self.dt)
