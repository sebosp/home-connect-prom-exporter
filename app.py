import logging
import os
import pprint

from flask import Flask, g, make_response, redirect, request
from homeconnect import HomeConnect

app = Flask(__name__)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_id = os.environ["HC_CLIENT_ID"]
client_secret = os.environ["HC_CLIENT_SECRET"]

logging.basicConfig(level=logging.INFO)


def get_hc():
    if "hc" not in g:
        g.hc = HomeConnect(client_id, client_secret, os.environ["HC_REDIR_URL"])
    return g.hc


@app.route("/login")
def login():
    # open this URL in your web browser
    hc = get_hc()
    return redirect(hc.get_authurl())


@app.route("/homeconnect")
def homeconnect_redir():
    hc = get_hc()
    auth_result = request.url
    hc.get_token(auth_result)
    # list the existing appliances
    return redirect("/list_appliances")


@app.route("/list_appliances")
def list_appliances():
    hc = get_hc()
    token = hc.token_load()
    if token is None:
        logging.error("token is None")
        return redirect("/login")
    appliances = hc.get_appliances()
    res = []
    for appliance in appliances:
        res.append(repr(appliance))
        if appliance.connected:
            res.append(repr(appliance.get_status()))
    return "<br/>".join(res)


@app.route("/metrics")
def prometheus_metrics():
    hc = get_hc()
    token = hc.token_load()
    res = [
        "# HELP hc_endpoint_connection whether the connection to home connect upstream is working",
        "# TYPE hc_endpoint_connection gauge",
    ]

    if token is None:
        logging.error("token is None")
        res.append("hc_endpoint_connection 0")
        return "\n".join(res)
    appliances = hc.get_appliances()
    appliance_states = []
    res.append(
        "# HELP hc_appliance_connected The connection state of the current appliance"
    )
    res.append("# TYPE hc_appliance_connected gauge")
    for appliance in appliances:
        appliance_state = {}
        appliance_state["brand"] = appliance.brand
        appliance_state["type"] = appliance.type
        appliance_state["name"] = appliance.name
        connect_status = "1" if appliance.connected else "0"
        appliance_state["status"] = {}
        res.append(
            f'hc_appliance_connected{{brand="{appliance.brand}", type="{appliance.type}", name="{appliance.name}"}} {connect_status}'
        )
        if appliance.connected:
            status = appliance.get_status()
            appliance_state["status"] = status
        appliance_states.append(appliance_state)
    # Show the common status oper state
    res.append("# HELP hc_bsch_common_status_oper_state The Bosch operation state")
    res.append("# TYPE hc_bsch_common_status_oper_state gauge")
    for appliance in appliance_states:
        status = appliance["status"]
        if "BSH.Common.Status.OperationState" in status:
            logging.info("%s", pprint.pformat(status))
            oper_state = status["BSH.Common.Status.OperationState"].get(
                "value", "unknown"
            )
            oper_state = oper_state.replace(
                "BSH.Common.EnumType.OperationState.", ""
            ).lower()
            res.append(
                'hc_bsch_common_status_oper_state{{brand="{}", type="{}", name="{}", value="{}"}} 1'.format(
                    appliance["brand"],
                    appliance["type"],
                    appliance["name"],
                    oper_state,
                )
            )

    # Show the common status door state
    res.append("# HELP hc_bsch_common_status_door_state The Bosch operation state")
    res.append("# TYPE hc_bsch_common_status_door_state gauge")
    for appliance in appliance_states:
        status = appliance["status"]
        if "BSH.Common.Status.DoorState" in status:
            door_state = (
                status["BSH.Common.Status.DoorState"]
                .get("value")
                .replace("BSH.Common.EnumType.DoorState.", "")
                .lower()
            )
            res.append(
                'hc_bsch_common_status_door_state{{brand="{}", type="{}", name="{}", value="{}"}} 1'.format(
                    appliance["brand"],
                    appliance["type"],
                    appliance["name"],
                    door_state,
                )
            )

    # Show the common status door state
    res.append("# HELP hc_bsch_oven_status_temperature The Bosch oven temperature")
    res.append("# TYPE hc_bsch_oven_status_temperature gauge")
    for appliance in appliance_states:
        status = appliance["status"]
        if "Cooking.Oven.Status.CurrentCavityTemperature" in status:
            temperature = status["Cooking.Oven.Status.CurrentCavityTemperature"].get(
                "value", None
            )
            if temperature is not None:
                res.append(
                    'hc_bsch_oven_status_temperature{{brand="{}", type="{}", name="{}"}} {}'.format(
                        appliance["brand"],
                        appliance["type"],
                        appliance["name"],
                        temperature,
                    )
                )
    response = make_response("\n".join(res))
    response.mimetype = "text/plain"
    return response
