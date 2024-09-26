FROM specifyconsortium/specify7-service:production@sha256:0b89c3eca81d43c706abb7a48b61ecd4f39aee34d9ed6c8b4f10a9eabe76831f
LABEL org.opencontainers.image.source=https://github.com/krkabol/specify7
LABEL description="Individual build of Specify 7 docker image"

COPY  --chown=specify:specify s6 /opt/Specify
COPY  --chown=specify:specify 0002_geo.py /opt/specify7/specifyweb/specify/migrations/0002_geo.py

USER root
RUN   mkdir /sock && \
    chown -R specify:specify /sock && \
    chown -R specify:specify /volumes/static-files  #done in original Docker file but somehow required

USER specify
CMD ["ve/bin/gunicorn", "-w", "3", "-b", "unix:/sock/docker.sock", "-t", "300", "specifyweb_wsgi"]