FROM python:3.8-alpine
LABEL maintainer="Jacob Tomlinson <jacob@tomlinson.email>"

WORKDIR /usr/src/app
ARG EXTRAS=.[all]

# Copy source
COPY . .

RUN apk update \
    && apk add --no-cache gcc g++ linux-headers musl-dev git openssh-client olm olm-dev \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir $EXTRAS \
    && apk del gcc g++ linux-headers musl-dev

EXPOSE 8080

CMD ["opsdroid", "start"]
