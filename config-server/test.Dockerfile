FROM python:3.6
LABEL maintainer="th10@sanger.ac.uk"

# Add fluent-bit

COPY --from=fluent/fluent-bit /fluent-bit /fluent-bit

# Install dependancies

ADD requirements.txt /docker/requirements.txt
RUN pip install -r /docker/requirements.txt

ADD test_requirements.txt /docker/test_requirements.txt
RUN pip install -r /docker/test_requirements.txt

# Add python scripts and set as workdir

ADD . /config-server
WORKDIR /config-server

# Add log file

RUN touch logs.log

CMD pytest