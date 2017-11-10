# -------------------------------------
# Docker container for building the app
# -------------------------------------
FROM node AS build
LABEL maintainer="th10@sanger.ac.uk"

# Install dependencies and http-server

ADD package.json /front-end/package.json
ADD package-lock.json /front-end/package-lock.json
WORKDIR /front-end
RUN npm install

# Add code files and build

ADD . /front-end
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