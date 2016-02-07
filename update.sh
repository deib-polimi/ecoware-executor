#!/bin/bash

grey=30
red=31
green=32
yellow=33
blue=34
purple=35
white=36

function colour_string
{
  typeset colour=$1
  shift
  printf "\e[1;%dm%s\e[0m" $colour "$*"
}

function colour_stringln
{
  colour_string "$*"
  printf "\n"
}

function do_run
{
  cmd="$*"
  printf "$cmd   "
  eval $cmd
  colour_stringln $green "[OK]"
}

git pull

now=$(date +"%d_%m_%Y")
cp executor.db ../executor_$now.db.bak

version="$(sqlite3 executor.db 'select version from db_version')"
while :
do
  if [ ! -f ./sql/updates/$(($version+1)).sql ]; then
    break
  fi
  version=$(($version+1))
  cmd="sqlite3 executor.db < ./sql/updates/$version.sql"
  do_run $cmd
done

# write last executed update to version
cmd="sqlite3 executor.db 'update db_version set version = $version'"
do_run $cmd

