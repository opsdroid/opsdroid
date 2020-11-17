# Exposing Opsdroid via tunnels

Many chat connectors require your Opsdroid instance to be accessible on the public internet. This is because
they send events to Opsdroid by calling HTTP endpoints directly.

You may choose to run Opsdroid on an internet facing machine such as a VM from a cloud vendor. You also have the option
to configure DNS (or at home [Dynamic DNS](https://www.duckdns.org/)) and open up ports on your router.

Alternatively you can tunnel traffic to Opsdroid through a variety of services. This page documents many of those tunneling options.

Most connectors will read the `web.base-url` config option and configure things for you, but this is not always the case.
For some connectors you may need to configure the URL of your bot yourself. See your specific connector's docs for info.

```eval_rst
.. note::
    As this page documents third-party tools and sevices it may become out of date. If you notice any errors or omissions please
    consider `raising a Pull Request <https://github.com/opsdroid/opsdroid/edit/master/docs/exposing.md>`_.
```

## Ngrok

**Type:** SaaS

**Cost:** $5/month (or free with random URLs)

**Source:** Proprietary

**Website:** [https://ngrok.com/](https://ngrok.com/)

Ngrok forwards any local web server to the internet via HTTP/HTTPS.

### Install

See the [official instructions](https://ngrok.com/download).


### Start tunnel

Opsdroid will run on port `8080` by default so let's start an HTTP tunnel to that port.

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

Add the following to your config.


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

It is likely that you are running Opsdroid as a service via something like systemd or Docker.

You can also run Ngrok as a service via [systemd](https://github.com/vincenthsu/systemd-ngrok) and [Docker](https://hub.docker.com/r/wernight/ngrok/).

## PageKite

**Type:** SaaS

**Cost:** Free (pay what you want)

**Source:** Open source ([GitHub](https://github.com/pagekite/PyPagekite/))

**Website:** [https://pagekite.net/](https://pagekite.net/)

PageKite forwards any local web server to the internet via HTTP/HTTPS.

### Install

See the [official instructions](https://pagekite.net/downloads).


### Start tunnel

Opsdroid will run on port `8080` by default so let's start an HTTP tunnel to that port.

```console
$ pagekite 8080 YOUR_CHOSEN_SUBDOMAIN.pagekite.me
```

You will then be prompted to answer some questions and enter your email address. Once you have clicked the
link in the email your session should start.

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

Add the following to your config.


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

It is likely that you are running Opsdroid as a service via something like systemd or Docker.

You can also run PageKite as a serivce, [see their FAQ](https://pagekite.net/wiki/HowTo/) for info.

## LocalTunnel

**Type:** SaaS

**Cost:** Free

**Source:** Open source ([GitHub](https://github.com/localtunnel/localtunnel))

**Website:** [https://localtunnel.github.io/www/](https://localtunnel.github.io/www/)

LocalTunnel forwards any local web server to the internet via HTTP/HTTPS.

### Install

See the [official instructions](https://localtunnel.github.io/www/).


### Start tunnel

Opsdroid will run on port `8080` by default so let's start an HTTP tunnel to that port.

```console
$ lt --port 8080 --subdomain YOUR_CHOSEN_SUBDOMAIN
your url is: https://LOCALTUNNEL_URL.loca.lt
```

### Configure Opsdroid

```console
$ opsdroid config edit
```

Add the following to your config.


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

localhost.run uses SSH to port forward a local service to an HTTP/HTTPS endpoint.

### Install

localhost.run uses SSH, so there is nothing to install.


### Start tunnel

Opsdroid will run on port `8080` by default so let's start an HTTP tunnel to that port.

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

Add the following to your config.


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

Inlets is a client/server application which tunnels traffic between them. You run the server on a machine with a public
IP and the client inside your network.

Inlets also [has support for Kubernetes](https://github.com/inlets/inlets-operator) to simplify exposing your services to the internet.

### Install

To install inlets you must install both the client and server applications.

On your local machine install the client following the [official instructions](https://github.com/inlets/inlets#get-inlets).

To install the server you must first create an exit-node server with a public IP address. Inlets [has many scripts](https://github.com/inlets/inlets/tree/master/hack) for creating one automatically for you from a variety of cloud vendors. Alternatively you can install it yourself on a VM and set it to run as a service with [this script](https://github.com/inlets/inlets/blob/master/hack/userdata.sh).

For the sake of this guide we are going to create an inlet on Digital Ocean, which will cost $5/month, using the official script. First we must [install doctl](https://github.com/digitalocean/doctl) and [authenticate](https://github.com/digitalocean/doctl#authenticating-with-digitalocean).

Then we can download and run the DO script.

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

Once you have your inlets server running you must take note of the server token. We can do this by using SSH to connect to the droplet and checking the logs.

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

Here we can see the SERVER_TOKEN in the output which we will need to open the tunnel.

### Start tunnel

Opsdroid will run on port `8080` by default so let's start an HTTP tunnel to that port. We need to specify the IP of the droplet, the local connection and the token.

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

Add the following to your config.


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

