FROM python:3-alpine
MAINTAINER Jacob Tomlinson <jacob@tom.linson.uk>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy source
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "opsdroid"]
