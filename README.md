# home-connect-prom-exporter

## Prerequisites

- Register Home Connect Application
- SSL cert (i.e. letsencrypt) on your web server of choice.
- Redir from your webserver HTTPs to the docker container port (i.e. :8080 as ran below.

## Building

$ docker build -t homeconnect:0.0.0 .

## Running

$ docker run -e HC_CLIENT_ID=$HC_CLIENT_ID -e HC_CLIENT_SECRET=$HC_CLIENT_SECRET -e HC_REDIR_URL=$HC_REDIR_URL -v app.py:/code/app.py -p 8080:8080 -it --rm homeconnect:0.0.0

## Flow

- Hit the login route: https://yourwebsiteroute/login (this should point to your container:8080/login)
- Follow the singlkey-id.com login and redir flow.
- It should ask permissions for your application.
- Your browser will be redirected to the container again, this time with a token and state parameters.
- NOTE: The token (JWT) will be stored inside the container and doesn't survive restarts.
- The /metrics endpoint should now work.

# Prometheus setup.

## Scrape

Because of the low amount of calls per day, the scrape interval should be low like this:
```yaml
scrape_configs:
  - job_name: 'homeconnect-exporter'
    # 1000 calls per day allowed.
    static_configs:
      - targets: ['dockerhost:8080']
    scrape_interval: '120s'
```

## Example alerts
(From `./homeconnect.yml`)

```yaml
groups:
- name: Bosch Appliance Door Open
  rules:
  - alert: BoschApplianceDoorOpen
    expr: hc_bsch_common_status_door_state{value="open"} > 0
    for: 1m
    labels:
      severity: page
    annotations:
      summary: Bosch Appliance Door Opened more than 1 minute
- name: Bosch Oven Temperature
  rules:
  - alert: Bosch Oven High Temperature
    expr: hc_bsch_oven_status_temperature{brand="Bosch", type="Oven", name="Oven"} > 100
    for: 5m
    labels:
      severity: page
    annotations:
      summary: Bosch Oven High Temperature more than 5 minutes
```

## Example circuitpython polling alerts
See `./code.py`

## Caveats

- Now and then need to restart due to low file desciptors.
- On restart container needs to hit again login flow (/login), a bit annoying.
