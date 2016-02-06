create table db_version (
  id integer primary key,
  version integer not null
);

insert into db_version (version) values (3);