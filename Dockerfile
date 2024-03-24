FROM --platform=linux/amd64 python:3.12

COPY tap_imdb/ ./tap_imdb/
COPY meltano.yml setup.py ./

RUN pip install -e .
RUN pip install meltano

RUN meltano lock --update --all
RUN meltano install extractor tap-imdb
RUN meltano install loader target-postgres

CMD ["meltano", "run", "tap-imdb", "target-postgres"]
