FROM python:3.8-alpine
LABEL maintainer="Jacob Tomlinson <jacob@tom.linson.uk>"

WORKDIR /usr/src/app
ARG EXTRAS=.[all]

# Copy source
COPY opsdroid opsdroid
COPY setup.py setup.py
COPY versioneer.py versioneer.py
COPY setup.cfg setup.cfg
COPY README.md README.md
COPY MANIFEST.in MANIFEST.in

RUN apk update \
&& apk add --no-cache gcc g++ linux-headers musl-dev git openssh-client olm olm-dev \
&& pip3 install --upgrade pip \
&& pip3 install --no-cache-dir --no-use-pep517 $EXTRAS \
&& apk del gcc g++ linux-headers musl-dev

EXPOSE 8080

CMD ["opsdroid", "start"]
