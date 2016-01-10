create table vm (
  id integer primary key,
  name varchar(255) unique not null,
  cpu inteeer not null,
  mem integer not null,
  docker_port integer unique not null
);

create table container (
  id integer primary key,
  vm_id integer not null,
  name varchar(255) unique not null,
  cpuset varchar(255) not null,
  mem integer not null,
  foreign key (vm_id) references vm (id)
);