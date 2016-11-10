FROM python:3-alpine
MAINTAINER Jacob Tomlinson <jacob@tom.linson.uk>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy source
COPY . .

RUN apk update && apk add git
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install -U tox

CMD ["python", "-m", "opsdroid"]
