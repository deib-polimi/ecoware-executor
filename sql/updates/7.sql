create table dependency (
  id integer primary key,
  from_tier_id integer not null,
  to_tier_name varchar(255) not null,
  unique(from_tier_id, to_tier_name),
  foreign key (from_tier_id) references tier (id)
);