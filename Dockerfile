FROM python:3.6-alpine
LABEL maintainer="Jacob Tomlinson <jacob@tom.linson.uk>"

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

RUN apk update && apk add git
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir .

EXPOSE 8080

CMD ["opsdroid"]
