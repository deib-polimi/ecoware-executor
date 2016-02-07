drop table tier_hook;

create table tier_hook (
  id integer primary key,
  tier_id integer not null,
  hook varchar(255) not null,
  unique(tier_id, hook),
  foreign key (tier_id) references tier (id)
);