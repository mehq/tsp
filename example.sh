#!/usr/bin/env bash

run_with_docker() {
  docker-compose up
}

run_without_docker() {
  python -m pip install --upgrade pip
  python -m pip install --requirement requirements.txt

  # Start the worker.
  python manage.py run_tsp_solver &

  # Start the API server.
  python manage.py runserver 8000 &
}

if [ "$1" = "docker" ]; then
  run_with_docker
else
  run_without_docker
fi

# Kill spawned process group.
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# Wait for the processes to complete.
wait
