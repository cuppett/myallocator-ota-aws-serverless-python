create table users (
  id varchar(256) primary key,
  password varchar(256) not null,
  myallocator_id varchar(128)
);

create table room_types(
  id varchar(36) primary key,
  user_id varchar(256) not null,
  title varchar(64) not null,
  occupancy TINYINT not null,
  detail TEXT,
  dorm BOOLEAN not null DEFAULT false,
  foreign key (user_id) references users(id) on delete cascade
);

create table bookings (
  id varchar(36) primary key,
  user_id varchar(256) not null,
  dttm datetime not null default now(),
  currency varchar(3) not null default 'USD',
  cancellation boolean not null default false,
  myallocator_guid varchar(36),
  foreign key (user_id) references users(id) on delete cascade
);

create table customers (
  email varchar(256) primary key,
  first_name varchar(64) not null,
  last_name varchar(64) not null,
  country varchar(2) not null default 'US'
);

create table booking_rooms (
  booking_id varchar(36) not null,
  room_type_id varchar(36) not null,
  dt date not null,
  description varchar(256),
  rate decimal(15,2) not null,
  rate_id varchar(36),
  primary key (booking_id, room_type_id, dt),
  foreign key (booking_id) references bookings(id),
  foreign key (room_type_id) references room_types(id)
);

create table booking_customers (
  booking_id varchar(36) not null,
  email varchar(256) not null,
  primary key (booking_id, email),
  foreign key (booking_id) references bookings(id),
  foreign key (email) references customers(email)
);
