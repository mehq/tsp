FROM python:3.9-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get upgrade --assume-yes

# Copy docker entrypoint script to appropriate location, give execute
# permissions.
COPY docker/tsp/entrypoint.production.sh /usr/local/sbin/entrypoint.sh
RUN chmod a+x /usr/local/sbin/entrypoint.sh

COPY docker/tsp/gunicorn.production.conf.py /etc/gunicorn.conf.py

COPY . /project

WORKDIR /project

RUN python -m pip install --upgrade pip
RUN python -m pip install --requirement requirements.txt

EXPOSE 8000

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]
CMD ["gunicorn", "tsp.wsgi", "--config", "/etc/gunicorn.conf.py", "--name", "tsp", "--log-level", "debug"]
