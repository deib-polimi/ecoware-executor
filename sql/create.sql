create table vm (
  id integer primary key,
  name varchar(255) unique not null,
  cpu integer not null,
  mem integer not null,
  host varchar(255) not null,
  docker_port integer not null,
  unique(host, docker_port)
);

create table container (
  id integer primary key,
  vm_id integer not null,
  name varchar(255) unique not null,
  cpuset varchar(255) not null,
  mem integer not null,
  foreign key (vm_id) references vm (id)
);

create table scale_hook (
  id integer primary key,
  container_id integer not null,
  hook varchar(255) not null,
  unique(container_id, hook),
  foreign key (container_id) references container (id)
);

create table db_version (
  id integer primary key,
  version integer not null
);

create table tier_hook (
  id integer primary key,
  container_id integer not null,
  hook varchar(255) not null,
  unique(container_id, hook),
  foreign key (container_id) references container (id)
);

create table tier (
  id integer primary key,
  name varchar(255) unique not null,
  image varchar(255) not null
);

insert into db_version (version) values (5);