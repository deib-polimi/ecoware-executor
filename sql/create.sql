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
  name varchar(255) not null,
  cpuset varchar(255) not null,
  mem integer not null,
  unique(vm_id, name),
  foreign key (vm_id) references vm (id)
);

create table db_version (
  id integer primary key,
  version integer not null
);

create table tier (
  id integer primary key,
  name varchar(255) unique not null,
  image varchar(255) not null
);

create table scale_hook (
  id integer primary key,
  tier_id integer not null,
  hook varchar(255) not null,
  unique(tier_id, hook),
  foreign key (tier_id) references tier (id)
);

create table tier_hook (
  id integer primary key,
  tier_id integer not null,
  hook varchar(255) not null,
  unique(tier_id, hook),
  foreign key (tier_id) references tier (id)
);

create table dependency (
  id integer primary key,
  from_tier_id integer not null,
  to_tier_name varchar(255) not null,
  unique(from_tier_id, to_tier_name),
  foreign key (from_tier_id) references tier (id)
);

insert into db_version (version) values (7);