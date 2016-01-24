#!/usr/bin/python
import sqlite3

def get_connection():
  return sqlite3.connect('executor.db')

def insert_vm(vm):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('insert into vm (name, cpu, mem, docker_port) values (?, ?, ?, ?)', 
      (vm.name, vm.cpu_cores, vm.mem_units, vm.docker_port))
    id = cur.lastrowid
    con.commit()
    return id
  finally:
    con.close()
  raise Error('Insert VM error')

def delete_vm(id):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('delete from vm where id = ?', (id,))
    con.commit()
  finally:
    con.close()

def insert_container(container):
  con = get_connection()
  try:
    cur = con.cursor()
    cur.execute('insert into container (vm_id, name, cpuset, mem) values (?, ?, ?, ?)', 
      (container.vm.id, container.name, ','.join(map(str, container.cpuset)), container.mem_units))
    id = cur.lastrowid
    con.commit()
    return id
  finally:
    con.close()
  raise Error('Insert container error')