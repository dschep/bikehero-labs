create table boundaries (
  boundary_id bigserial primary key,
  boundary geometry,
  "name" text,
  created timestamp default now()
);