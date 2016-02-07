create table tier (
  id integer primary key,
  name varchar(255) unique not null,
  image varchar(255) not null
);