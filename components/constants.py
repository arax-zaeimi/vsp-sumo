
import os
import sys


MAPS_PATH = "\\map"
TRAFFIC_PATH = "\\scenario"
TRIPS_OUTPUT_PATH = os.getcwd() + TRAFFIC_PATH + '\\output.tripinfo.xml'
DEFAULT_SUMO_CONFIG_PATH = os.getcwd() + TRAFFIC_PATH + '\\osm.sumocfg'
DEFAULT_NET_PATH = os.getcwd() + TRAFFIC_PATH + '\\osm.net.xml'
PREFIX = "demo"
OCCUPATION_PROBABILITY = 0.5
SIMULATION_DELAY = "500"
SIMULATION_CLIENTS = "1"
SIMULATION_STEP_LENGTH = "0.001"
# ALLOWED_VEHICLES = ('public_emergency', 'public_authority', 'public_army', 'public_transport', 'transport', 'private', 'emergency', 'authority',
#                     'army', 'vip', 'passenger', 'hov', 'taxi', 'bus', 'coach', 'delivery', 'truck', 'trailer', 'motorcycle', 'moped', 'bicycle', 'evehicle')
ALLOWED_VEHICLES = ('passenger', 'evehicle')
MAX_SEARCH_RADIUS = 30

# this is the id of vType that is defined in route files.
SERVICE_VEHICLE_TYPE = 'passenger1'
MAP_FILE_NAME = '_bbox.osm.xml'


PORT = 8883
SUMO_HOME = os.path.realpath(os.environ.get(
    "SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
sys.path.append(os.path.join(SUMO_HOME, "tools"))
try:
    from sumolib import checkBinary  # noqa
except ImportError:
    def checkBinary(name):
        return name
NETCONVERT = checkBinary("netconvert")
SUMO = checkBinary("sumo")
SUMOGUI = checkBinary("sumo-gui")


COMMAND_NEW_VEHICLE = 'ADD_VEHICLE'
COMMAND_NEW_VEHICLES = 'ADD_VEHICLES'
COMMAND_NEW_DESTINATION = 'NEW_DESTINATION'
COMMAND_ADD_SEGMENT = 'ADD_SEGMENT'
COMMAND_REMOVE_SEGMENT = 'REMOVE_SEGMENT'
