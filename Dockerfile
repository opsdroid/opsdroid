FROM python:3.7-alpine
LABEL maintainer="Jacob Tomlinson <jacob@tom.linson.uk>"

WORKDIR /usr/src/app

# Copy source
COPY opsdroid opsdroid
COPY setup.py setup.py
COPY versioneer.py versioneer.py
COPY setup.cfg setup.cfg
COPY requirements.txt requirements.txt
COPY README.md README.md
COPY MANIFEST.in MANIFEST.in

RUN apk update \
&& apk add --no-cache gcc g++ linux-headers musl-dev git openssh-client olm olm-dev \
&& pip3 install --upgrade pip \
&& pip3 install --no-cache-dir --no-use-pep517 . \
&& apk del gcc g++ linux-headers musl-dev

EXPOSE 8080

CMD ["opsdroid", "start"]
