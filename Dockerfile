FROM python:3.7-alpine
LABEL maintainer="Jacob Tomlinson <jacob@tom.linson.uk>"

RUN apk add --no-cache gcc musl-dev alpine-sdk libstdc++
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy source
COPY opsdroid opsdroid
COPY setup.py setup.py
COPY versioneer.py versioneer.py
COPY setup.cfg setup.cfg
COPY requirements.txt requirements.txt
COPY README.md README.md
COPY MANIFEST.in MANIFEST.in

RUN apk update && apk add --no-cache git openssh-client
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --no-use-pep517 .
RUN pip3 install dialogflow
RUN apk del gcc musl-dev alpine-sdk

EXPOSE 8080

CMD ["opsdroid", "start"]
