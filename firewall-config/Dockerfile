FROM python:3.6
LABEL maintainer="th10@sanger.ac.uk"

# Install dependancies

ADD requirements.txt /docker/requirements.txt
RUN pip install -r /docker/requirements.txt

# Add python scripts and set as workdir

ADD . /firewall-config
WORKDIR /firewall-config

CMD python -m firewallconfig
