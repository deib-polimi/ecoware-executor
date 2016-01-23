#!/usr/bin/python
import sqlite3

def get_connection():
  return sqlite3.connect('executor.db')

def insert_vm(vm):
  con = get_connection()
  try:
    cursor = con.cursor()
    cursor.execute('insert into vm (name, cpu, mem, docker_port) values (?, ?, ?, ?)', 
      (vm.name, vm.cpu_cores, vm.mem_units, vm.docker_port))
    id = cursor.lastrowid
    con.commit()
    return id
  finally:
    con.close()
  raise Error('Insert VM error')