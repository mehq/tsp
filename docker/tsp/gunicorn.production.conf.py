# pylint: disable=invalid-name

import multiprocessing
import os

GUNICORN_WORKER_COUNT = int(os.environ.get("GUNICORN_WORKER_COUNT", "0"), 10)
HOST = os.environ.get("HOST", "0.0.0.0")  # nosec
PORT = os.environ.get("PORT", "8000")

bind = f"{HOST}:{PORT}"
workers = GUNICORN_WORKER_COUNT or multiprocessing.cpu_count() * 2 + 1

# access_logfile = "/var/log/myfolab_api/gunicorn.log"
# error_logfile = "/var/log/myfolab_api/gunicorn.err.log"
