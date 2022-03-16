#!/usr/bin/env python3

# This is a WoT example of Tuya Smart Humidifier using WoTPy.

import json
import logging
import time
from distutils.util import strtobool

import tornado.gen
from tornado.ioloop import IOLoop

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

from tuya_connector import TuyaOpenAPI, TUYA_LOGGER

CATALOGUE_PORT = 9090
WEBSOCKET_PORT = 9393
HTTP_PORT = 9494

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

ACCESS_ID = "<access_id>"
ACCESS_KEY = "<access_key>"
API_ENDPOINT = "https://openapi.tuyaus.com"
DEVICE_ID ="<device_id>"
openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()

TD = {
    "title": "TuyaSmartHumidifier",
    "id": "urn:wot:TuyaSmartHumidifier",
    "description": "This is a WoT example of Tuya Smart Humidifier using WoTPy.",
    "@context": [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    "properties": {
        "state": {
            "type": "object",
            "properties": {
                "switch": {
                    "type": "boolean"
                },
                "countdown": {
                    "type": "string",
                    "enum": ["cancel", "1", "3", "6"]
                },
                "mode": {
                    "type": "string",
                    "enum": ["interval", "continuous"]
                },
                "switch_spray": {
                    "type": "boolean"
                },
                "moodlighting": {
                    "type": "number",
                    'minimum': 1,
                    'maximum': 5
                },
                "colour_data": {
                    "type": "number",
                    'minimum': 0,
                    'maximum': 255
                }
            }
        }
    },
    "actions": {
        "updateStatus": {
            "description": "updateStatus",
            "input" :{
                "type": "object",
                "properties": {
                    "switch": {
                        "type": "boolean"
                    },
                    "countdown": {
                        "type": "string",
                        "enum": ["cancel", "1", "3", "6"]
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["interval", "continuous"]
                    },
                    "switch_spray": {
                        "type": "boolean"
                    },
                    "moodlighting": {
                        "type": "number",
                        'minimum': 1,
                        'maximum': 5
                    },
                    "colour_data": {
                        "type": "number",
                        'minimum': 0,
                        'maximum': 255
                    }
                }
            }
        }
    }
}

@tornado.gen.coroutine
def main():
    LOGGER.info("Creating WebSocket server on: {}".format(WEBSOCKET_PORT))
    ws_server = WebsocketServer(port=WEBSOCKET_PORT)

    LOGGER.info("Creating HTTP server on: {}".format(HTTP_PORT))
    http_server = HTTPServer(port=HTTP_PORT)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(ws_server)
    servient.add_server(http_server)

    LOGGER.info("Starting servient")
    wot = yield servient.start()

    LOGGER.info("Exposing and configuring Thing")

    exposed_thing = wot.produce(json.dumps(TD))

    async def status_read_handler():
        response = openapi.get("/v1.0/iot-03/devices/{}/status".format(DEVICE_ID))
        data = json.dumps(response)
        json_data = json.loads(data)
        result = {}
        for x in range(len(json_data["result"])):
            result.update({json_data["result"][x]['code']:json_data["result"][x]["value"]})

        STATUS=({
            'switch': result.get("switch"),
            'countdown': result.get("countdown"),
            'mode': (result.get("mode") if result.get("mode")!= None else "continuous"),
            'switch_spray': result.get("switch_spray"),
            'moodlighting': result.get("moodlighting"),
            'colour_data': result.get("colour_data"),
        })

        return STATUS

    exposed_thing.set_property_read_handler('state', status_read_handler)

    async def sendStatus_action_handler(params):
        params = params['input'] if params['input'] else {}

        resources = await exposed_thing.read_property('state')
        switch = resources['switch']
        countdown = resources['countdown']
        mode = resources['mode']
        switch_spray = resources['switch_spray']
        moodlighting = resources['moodlighting']
        colour_data = resources['colour_data']

        switch = bool(strtobool(params.get('switch', switch)))
        countdown = params.get('countdown', countdown)
        mode = params.get('mode', mode)
        switch_spray = bool(strtobool(params.get('switch_spray', switch_spray)))
        moodlighting = params.get('moodlighting', moodlighting)
        colour_data = params.get('colour_data', colour_data)

        commands = {'commands': [{"code": "switch", "value": switch},{"code": "countdown", "value": countdown},{"code": "mode", "value": mode},{"code": "moodlighting", "value": moodlighting},{"code": "colour_data", "value": colour_data},{"code": "switch_spray", "value": switch_spray}]}
        openapi.post('/v1.0/iot-03/devices/{}/commands'.format(DEVICE_ID), commands)

        return {'result': True, 'message': [switch,countdown,mode,switch_spray,moodlighting,colour_data]}

    exposed_thing.set_action_handler('updateStatus', sendStatus_action_handler)

    exposed_thing.expose()

if __name__ == "__main__":
    LOGGER.info("Starting loop")
    IOLoop.current().add_callback(main)
    IOLoop.current().start()
