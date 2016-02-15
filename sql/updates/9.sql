drop table container;

create table container (
  id integer primary key,
  vm_id integer not null,
  name varchar(255) not null,
  cpuset varchar(255) not null,
  mem integer not null,
  unique(vm_id, name),
  foreign key (vm_id) references vm (id)
);