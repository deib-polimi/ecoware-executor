#!/usr/bin/python
import sqlite3

def get_connection():
  return sqlite3.connect('executor.db')