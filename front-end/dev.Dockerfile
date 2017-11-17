FROM node:8.9

WORKDIR /front-end

CMD ./node_modules/.bin/webpack-dev-server --port 80 --host 0.0.0.0