# Exposing Opsdroid via tunnels

많은 챗 커넥터가 공용 인터넷에 접근하기 위해 opsdroid의 인스턴스를 필요로 합니다. HTTP 엔드포인트를 바로 호출하는 것으로 opsdroid에 이벤트를 보내기 때문입니다.

클라우드 기업의 가상머신 같은 인터넷을 대면하는 머신으로 opsdroid를 작동하는걸 고를 것입니다. 또한 DNS를(또는 집에서 [Dynamic DNS](https://www.duckdns.org/)) 설정하여 라우터의 포트를 여는 선택지도 있습니다.

또는 다양한 서비스를 통해 트래픽을 opsdroid로 터널링할 수 있습니다. 이 페이지는 많은 터널링 옵션을 설명합니다.

대부분의 커넥터는 `web.base-url` 설정 옵션을 읽어들이고 설정을 해주지만, 항상 그런 케이스는 아닙니다.
일부 커넥터는 봇의 URL을 직접 설정해줘야 할 것입니다. 정보를 위해 특정 커넥터의 문서를 확인해보세요.

```eval_rst
.. note::
    이 페이지는 타사의 툴과 서비스를 기록하므로 오래된 문서일 수 있습니다. If you notice any errors or omissions please
    consider `raising a Pull Request <https://github.com/opsdroid/opsdroid/edit/master/docs/exposing.md>`_.
```

## Ngrok

**Type:** SaaS

**Cost:** $5/month (or free with random URLs)

**Source:** Proprietary

**Website:** [https://ngrok.com/](https://ngrok.com/)

Ngrok은 HTTP/HTTPS를 통해서 로컬 웹서버를 인터넷으로 포워딩합니다.

### Install

See the [official instructions](https://ngrok.com/download).


### Start tunnel

opsdroid는 기본값으로 8080포트에서 동작할 것이므로 포트에 HTTP 터널링을 시작해봅시다.

```console
$ ngrok http 8080
ngrok by @inconshreveable                                                                   (Ctrl+C to quit)

Session Status                online
Session Expires               7 hours, 59 minutes
Version                       2.3.35
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    http://NGROK_URL.ngrok.io -> http://localhost:8080
Forwarding                    https://NGROK_URL.ngrok.io -> http://localhost:8080

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

다음을 환경 설정에 추가해주세요.


```yaml
web:
  base-url: https://NGROK_URL.ngrok.io  # Whatever your https URL is in the ngrok output
```

```eval_rst
.. warning::
    If you use a free Ngrok account the URL will be randomised every time your start Ngrok and you will need
    to update your Opsdroid config and restart.
```

### Run Opsdroid

```console
$ opsdroid start
INFO opsdroid.logging: ========================================
INFO opsdroid.web: Started web server on https://NGROK_URL.ngrok.io
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

### Running as a service

systemd나 도커 등을 통해 opsdroid를 서비스로 실행하고 있을것으로 예상됩니다.

Ngrok 또한 [systemd](https://github.com/vincenthsu/systemd-ngrok)와 [Docker](https://hub.docker.com/r/wernight/ngrok/)를 통해 서비스로써 실행할 수 있습니다.

## PageKite

**Type:** SaaS

**Cost:** Free (pay what you want)

**Source:** Open source ([GitHub](https://github.com/pagekite/PyPagekite/))

**Website:** [https://pagekite.net/](https://pagekite.net/)

PageKite는 HTTP/HTTPS를 통해서 로컬 웹서버를 인터넷으로 포워딩합니다.

### Install

[official instructions](https://pagekite.net/downloads)를 확인하세요.


### Start tunnel

opsdroid는 기본값으로 8080포트에서 동작할 것이므로 포트에 HTTP 터널링을 시작해봅시다.

```console
$ pagekite 8080 YOUR_CHOSEN_SUBDOMAIN.pagekite.me
```

그 다음 몇 가지 질문에 대답하고 이메일 주소를 입력하라는 메시지가 표시될 겁니다. 일단 이메일에 있는 링크를 클릭했다면 세션이 시작되어야 합니다.

```
>>> Hello! This is pagekite v1.5.2.201011.                      [CTRL+C = Stop]
    Connecting to front-end relay xxx.xxx.xxx.xxx:443 ...
     - Relay supports 10 protocols on 19 public ports.
     - Raw TCP/IP (HTTP proxied) kites are available.
     - To enable more logging, add option: --logfile=/path/to/logfile
    Abuse/DDOS protection: Relaying traffic for up to 5 clients per 10800s.
    Quota: You have 31 days, 5.0 tunnels left.
~<> Flying localhost:8080 as https://YOUR_CHOSEN_SUBDOMAIN.pagekite.me/
    xxx.xxx.xxx.xxx < http://YOUR_CHOSEN_SUBDOMAIN.pagekite.me:443 (localhost:8080)
 << pagekite.py [flying]   Kites are flying and all is well.
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

다음을 환경 설정에 추가해주세요.


```yaml
web:
  base-url: https://YOUR_CHOSEN_SUBDOMAIN.pagekite.me
```

### Run Opsdroid

```console
$ opsdroid start
INFO opsdroid.logging: ========================================
INFO opsdroid.web: Started web server on https://YOUR_CHOSEN_SUBDOMAIN.pagekite.me
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

### Running as a service

systemd나 도커 등을 통해 opsdroid를 서비스로 실행하고 있을것으로 예상됩니다.

PageKite 또한 서비스로써 실행할 수 있습니다. [see their FAQ](https://pagekite.net/wiki/HowTo/) 를 확인하세요.

## LocalTunnel

**Type:** SaaS

**Cost:** Free

**Source:** Open source ([GitHub](https://github.com/localtunnel/localtunnel))

**Website:** [https://localtunnel.github.io/www/](https://localtunnel.github.io/www/)

LocalTunnel는 HTTP/HTTPS를 통해서 로컬 웹서버를 인터넷으로 포워딩합니다.

### Install

[official instructions](https://localtunnel.github.io/www/)를 확인하세요.


### Start tunnel

opsdroid는 기본값으로 8080포트에서 동작할 것이므로 포트에 HTTP 터널링을 시작해봅시다.

```console
$ lt --port 8080 --subdomain YOUR_CHOSEN_SUBDOMAIN
your url is: https://LOCALTUNNEL_URL.loca.lt
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

다음을 환경 설정에 추가해주세요.


```yaml
web:
  base-url: https://LOCALTUNNEL_URL.loca.lt
```

```eval_rst
.. warning::
    Without the ``--subdomain`` flag the URL will be randomised every time your start lt and you will need
    to update your Opsdroid config and restart.
```

### Run Opsdroid

```console
$ opsdroid start
INFO opsdroid.logging: ========================================
INFO opsdroid.web: Started web server on https://LOCALTUNNEL_URL.loca.lt
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

## localhost.run

**Type:** SaaS

**Cost:** Free ($3.50/month for custom domains)

**Source:** NA

**Website:** [http://localhost.run/](http://localhost.run/)

localhost.run 은 HTTP/HTTPS 엔드포인트로 로컬 서비스를 포워딩하기 위해 SSH를 포트로 사용합니다.

### Install

localhost.run은 SSH를 사용하므로, 설치할 것이 없습니다.


### Start tunnel

opsdroid는 기본값으로 8080포트에서 동작할 것이므로 포트에 HTTP 터널링을 시작해봅시다.

```console
$ ssh -R 80:localhost:8080 ssh.localhost.run
===============================================================================
Welcome to localhost.run!

Head over to https://twitter.com/localhost_run and give us a follow for the
hottest SSH port forwarded local dev env news.

**You need a SSH key to access this service.**

Github has a great howto, follow along with it to get prepared for the change:
https://help.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

**CUSTOM DOMAINS ARE HERE AND I'M SO EXCITED**
I've been working hard on custom domains and I'm soft launching the custom
domain plan option to existing users. If you own a domain name that you'd like
localhost.run on visit https://admin.localhost.run/ to look at the plan
and set it up.

===============================================================================

Connect to http://LOCALHOST_RUN_URL.localhost.run
{"domain": "LOCALHOST_RUN_URL.localhost.run", "listen_port": 80, "status": "success", "message": "Connect to http://LOCALHOST_RUN_URL.localhost.run"}
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

다음을 환경 설정에 추가해주세요.


```yaml
web:
  base-url: https://LOCALHOST_RUN_URL.localhost.run
```

```eval_rst
.. warning::
    Unless you subscribe for custom domains the subdomain will be randomised each time you connect and
    you will need to update your Opsdroid config and restart.
```

### Run Opsdroid

```console
$ opsdroid start
INFO opsdroid.logging: ========================================
INFO opsdroid.web: Started web server on https://LOCALHOST_RUN_URL.localhost.run
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

## Inlets

**Type:** Self hosted

**Cost:** Free + the cost of your exit-node VM ([Hosted PRO version](https://inlets.dev/) available from $20/month)

**Source:** Open Source ([GitHub](https://github.com/inlets/inlets))

**Website:** [https://docs.inlets.dev/](https://docs.inlets.dev/)

Inlets은 서로간의 트래픽을 터널링하는 클라이언트/서버 어플리케이션입니다. 공용 IP와 네트워크 안에 클라이언트가 있는 컴퓨터에서 서버를 실행합니다.


Inlets은 또한 서비스를 인터넷에 노출시키는 것을 간소화하기 위해 [Kubernetes를 위한 지원](https://github.com/inlets/inlets-operator)을 하고 있습니다

### Install

Inlets을 설치하기 위해서 클라이언트와 서버 어플리케이션 모두 설치해야 합니다

로컬 컴퓨터에는 다음 지침을 따르는 클라이언트를 설치하세요 [official instructions](https://github.com/inlets/inlets#get-inlets).

서버를 설치하기 위해서 공용 IP주소를 가진 exit-node 서버를 생성해야 합니다. Inlet은 다양한 클라우드 기업으로부터 자동적으로 하나를 생성해주는[많은 스크립트](https://github.com/inlets/inlets/tree/master/hack)가 있습니다. 또는 [이 스크립트로](https://github.com/inlets/inlets/blob/master/hack/userdata.sh)서비스로써 실행시키기 위해 가상머신에 직접 설치하고 설정할 수 있습니다.

이 가이드를 위해 디지털 오션에 공식 스크립트를 사용하여 한달에 5$ 비용이 드는  inlet을 생성할 것입니다. 먼저 [doctl 설치와](https://github.com/digitalocean/doctl) and [인증](https://github.com/digitalocean/doctl#authenticating-with-digitalocean)을 해야합니다.

그 다음 DO스크립트를 다운로드하고 실행할 수 있습니다.

```console
$ git clone https://github.com/inlets/inlets.git
$ cd inlets
$ ./hack/provision-digitalocean.sh
Creating: DROPLET_NAME
==============================
Droplet: DROPLET_NAME has been created
IP: DROPLET_IP
Login: ssh root@DROPLET_IP
==============================
To destroy this droplet run: doctl compute droplet delete -f DROPLET_NAME
```

Once you have your inlets server running you must take note of the server token. 일단 inlets 서버가 실행되면 서버 토큰을 기록해야 합니다. SSH를 사용하여 droplet과 연결하고 로그를 확인하여 수행할 수 있습니다.

```console
$ ssh root@DROPLET_IP
# systemctl status inlets
● inlets.service - Inlets Server Service
   Loaded: loaded (/etc/systemd/system/inlets.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2020-11-02 12:24:15 UTC; 3min 41s ago
 Main PID: 1789 (inlets)
   CGroup: /system.slice/inlets.service
           └─1789 /usr/local/bin/inlets server --port=80 --token=SERVER_TOKEN

Nov 02 12:24:15 inlets7c442412 systemd[1]: Started Inlets Server Service.
Nov 02 12:24:15 inlets7c442412 inlets[1789]: 2020/11/02 12:24:15 Welcome to inlets.dev! Find out more at htt
Nov 02 12:24:15 inlets7c442412 inlets[1789]: 2020/11/02 12:24:15 Starting server - version 2.7.10
Nov 02 12:24:15 inlets7c442412 inlets[1789]: 2020/11/02 12:24:15 Server token: "SERVER_TOKEN
Nov 02 12:24:15 inlets7c442412 inlets[1789]: 2020/11/02 12:24:15 Control Plane Listening on :80
Nov 02 12:24:15 inlets7c442412 inlets[1789]: 2020/11/02 12:24:15 Data Plane Listening on :80
```

여기서 출력내용에 터널을 열기위해 필요한 SERVER_TOKEN을 볼 수 있습니다.

### Start tunnel

opsdroid는 기본값으로 8080포트에서 동작할 것이므로 포트에 HTTP 터널링을 시작해봅시다. droplet의 IP, 로컬 연결, 토큰을 지정해줘야 합니다.

```console
$ inlets client \
 --remote=DROPLET_IP \
 --upstream=http://127.0.0.1:8080 \
 --token=SERVER_TOKEN
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

다음을 환경 설정에 추가해주세요.


```yaml
web:
  base-url: http://DROPLET_IP
```

```eval_rst
.. warning::
    Only HTTP traffic has been configured here. For secure HTTPS you will need to use a reverse proxy on the exit-node and configure
    something like LetsEncrypt. See this `tutorial using Caddy <https://blog.alexellis.io/https-inlets-local-endpoints/>`_.
```

### Run Opsdroid

```console
$ opsdroid start
INFO opsdroid.logging: ========================================
INFO opsdroid.web: Started web server on http://DROPLET_IP
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

