# -------------------------------------
# Docker container for building the app
# -------------------------------------
FROM node:8.9 AS build
LABEL maintainer="th10@sanger.ac.uk"

# Install dependencies and http-server

ADD package.json /front-end/package.json
ADD package-lock.json /front-end/package-lock.json
WORKDIR /front-end
RUN npm install

# Add code files

ADD . /front-end

# Specify the configuration variables

ARG CONFIG_SERVER
ARG ROUTING_SERVER

# Build the files

RUN npm run-script build

# -------------------------------------
# Production docker container
# -------------------------------------
FROM httpd:2.4

COPY --from=build /front-end/index.html /usr/local/apache2/htdocs/
COPY --from=build /front-end/bundle.js /usr/local/apache2/htdocs/
COPY --from=build /front-end/bundle.css /usr/local/apache2/htdocs/
COPY --from=build /front-end/fonts/* /usr/local/apache2/htdocs/fonts/
COPY --from=build /front-end/img/* /usr/local/apache2/htdocs/img/