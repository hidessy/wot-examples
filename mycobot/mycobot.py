#!/usr/bin/env python3

# This is a WoT example of myCobot using WoTPy.

import json
import logging

import tornado.gen
from tornado.ioloop import IOLoop

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

from pymycobot import MyCobot
from pymycobot.genre import Angle

CATALOGUE_PORT = 9090
WEBSOCKET_PORT = 9393
HTTP_PORT = 9494

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

mycobot = MyCobot('/dev/cu.SLAB_USBtoUART')

TD = {
    "title": "mycobot",
    "id": "urn:wot:mycobot",
    "description": "This is a WoT example of mycobot using WoTPy.",
    "@context": [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    "properties": {
        "angles": {
            "type": "object",
            "properties": {
                "angle1": {
                    "type": "number",
                    'minimum': -165,
                    'maximum': 165
                },
                "angle2": {
                    "type": "number",
                    'minimum': -165,
                    'maximum': 165
                },
                "angle3": {
                    "type": "number",
                    'minimum': -165,
                    'maximum': 165
                },
                "angle4": {
                    "type": "number",
                    'minimum': -165,
                    'maximum': 165
                },
                "angle5": {
                    "type": "number",
                    'minimum': -165,
                    'maximum': 165
                },
                "angle6": {
                    "type": "number",
                    'minimum': -175,
                    'maximum': 175
                }
            }
        }
    },
    "actions": {
        "sendAngles": {
            "description": "sendAngle",
            "input" :{
                "type": "object",
                "properties": {
                    "angle1": {
                        "type": "number",
                        'minimum': -165,
                        'maximum': 165
                    },
                    "angle2": {
                        "type": "number",
                        'minimum': -165,
                        'maximum': 165
                    },
                    "angle3": {
                        "type": "number",
                        'minimum': -165,
                        'maximum': 165
                    },
                    "angle4": {
                        "type": "number",
                        'minimum': -165,
                        'maximum': 165
                    },
                    "angle5": {
                        "type": "number",
                        'minimum': -165,
                        'maximum': 165
                    },
                    "angle6": {
                        "type": "number",
                        'minimum': -175,
                        'maximum': 175
                    },
                    "speed": {
                        "type": "integer",
                        'minimum': 0,
                        'maximum': 100
                    }
                }
            }
        },
        "releaseServos": {
            "input" :{
                "type": "object",
                "properties": {
                    "release": {
                        "type": "boolean",
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

    async def angle_read_handler():
        angles = mycobot.get_angles()

        ANGLES=({
            'angle1': angles[0],
            'angle2': angles[1],
            'angle3': angles[2],
            'angle4': angles[3],
            'angle5': angles[4],
            'angle6': angles[5],
        })

        return ANGLES

    exposed_thing.set_property_read_handler('angles', angle_read_handler)

    async def sendAngle_action_handler(params):
        params = params['input'] if params['input'] else {}

        resources = await exposed_thing.read_property('angles')
        angle1 = resources['angle1']
        angle2 = resources['angle2']
        angle3 = resources['angle3']
        angle4 = resources['angle4']
        angle5 = resources['angle5']
        angle6 = resources['angle6']
        speed = 50

        angle1 = params.get('angle1', angle1)
        angle2 = params.get('angle2', angle2)
        angle3 = params.get('angle3', angle3)
        angle4 = params.get('angle4', angle4)
        angle5 = params.get('angle5', angle5)
        angle6 = params.get('angle6', angle6)
        speed = params.get('speed', speed)

        mycobot.send_angles([angle1,angle2,angle3,angle4,angle5,angle6], speed)

        return {'result': True, 'message': [angle1,angle2,angle3,angle4,angle5,angle6]}

    exposed_thing.set_action_handler('sendAngles', sendAngle_action_handler)

    async def release_action_handler(params):
        params = params['input'] if params['input'] else {}

        release = "True"
        release = params.get('release', release)

        if release == "True":
            mycobot.release_all_servos()

        return {'result': True, 'message': release}

    exposed_thing.set_action_handler('releaseServos', release_action_handler)

    exposed_thing.expose()

if __name__ == "__main__":
    LOGGER.info("Starting loop")
    IOLoop.current().add_callback(main)
    IOLoop.current().start()
