#!/bin/sh

error() {
  echo "\033[0;31m$1\033[0m"
}

port() {
  lsof -i:$1 | grep LISTEN | awk '{print $2}' | xargs kill -9
  error "PORT $1 is killed"
}

# kill port
for arg in "$@"; do
  port $arg
done
