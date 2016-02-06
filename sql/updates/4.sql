create table tier_hook (
  id integer primary key,
  container_id integer not null,
  hook varchar(255) not null,
  unique(container_id, hook),
  foreign key (container_id) references container (id)
);