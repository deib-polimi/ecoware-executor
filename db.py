#!/usr/bin/python
import sqlite3

def get_connection():
  return sqlite3.connect('executor.db')

def insert_vm(vm):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('insert into vm (name, cpu, mem, host, docker_port) values (?, ?, ?, ?, ?)', 
      (vm.name, vm.cpu_cores, vm.mem_units, vm.host, vm.docker_port))
    id = cur.lastrowid
    con.commit()
    return id
  finally:
    con.close()
  raise Exception('Insert VM error')

def delete_vm(id):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('delete from container where vm_id = ?', (id,))
    cur.execute('delete from vm where id = ?', (id,))
    con.commit()
  finally:
    con.close()

def insert_container(container):
  con = get_connection()
  try:
    cur = con.cursor()
    cpuset = ','.join(map(str, container.cpuset))
    cur.execute('insert into container (vm_id, name, cpuset, mem) values (?, ?, ?, ?)', 
      (container.vm.id, container.name, cpuset, container.mem_units))
    id = cur.lastrowid
    for hook in container.scale_hooks:
      cur.execute('insert into scale_hook (container_id, hook) values (?, ?)',
        (id, hook))
    con.commit()
    return id
  finally:
    con.close()
  raise Exception('Insert container error')

def delete_container(id):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('delete from container where id = ?', (id,))
    cur.execute('delete from scale_hook where container_id = ?', (id,))
    con.commit()
  finally:
    con.close()

def update_container(container):
  con = get_connection()
  try:
    cpuset = ','.join(map(str, container.cpuset))
    cur = con.cursor()
    cur.execute('update container set cpuset = ?, mem = ? where id = ?', (cpuset, container.mem, container.id))
    cur.execute('delete from scale_hook where container_id = ?', (container.id,))
    for hook in container.scale_hooks:
      cur.execute('insert into scale_hook (container_id, hook) values (?, ?)',
        (container.id, hook))
    con.commit()
  finally:
    con.close()

def insert_tier(tier):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('insert into tier (name, image) values (?, ?)', 
      (tier.name, tier.image))
    tier.id = cur.lastrowid
    for hook in tier.tier_hooks:
      cur.execute('insert into tier_hook (tier_id, hook) values(?, ?)',
        (tier.id, hook))
    con.commit()
    return tier.id
  finally:
    con.close()
  raise Exception('Insert tier error')

def delete_tiers():
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('delete from tier')
    cur.execute('delete from tier_hook')
    con.commit()
    return
  finally:
    con.close()
  raise Exception('Delete tiers error')