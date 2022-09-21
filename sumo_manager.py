from asyncio import constants
from distutils.log import error
from msilib.schema import Component
import optparse
import os
import sys

import pandas as pd
import sumolib
import traci
from pandas import DataFrame
from sumolib.net import Net

from components.convertaddress import geocodeByNominatim as geocode
from components.data import clear_changes, get_changes
from components.constants import (PORT, SIMULATION_DELAY, SIMULATION_STEP_LENGTH, SUMO,
                                  SUMOGUI, ALLOWED_VEHICLES, MAX_SEARCH_RADIUS, SERVICE_VEHICLE_TYPE)
from components.constants import change_types

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

# I am using this variable as a cache for the network file. I do not want to read the file each time I access the property.
# So, I read the file for the first time and cache it into memory, then will read the memory for next accesses.
SIMULATION_NET_CACHE = None


def load_simulation_network():
    global SIMULATION_NET_CACHE
    if SIMULATION_NET_CACHE == None:
        SIMULATION_NET_CACHE = sumolib.net.readNet(get_options().net)

    return SIMULATION_NET_CACHE


def get_options():

    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui",
                          action="store_true",
                          default=False,
                          help="run the commandline version of sumo")

    opt_parser.add_option("-c", "--config",
                          action="store",
                          default=False,
                          help="sumo configuration file")

    opt_parser.add_option("--map",
                          action="store",
                          default=False,
                          help="path to osm map file")

    opt_parser.add_option("--net",
                          action="store",
                          default=False,
                          help="path to simulation network file")

    opt_parser.add_option("--schedule",
                          action="store",
                          default=False,
                          help="path to schedule file")

    opt_parser.add_option("--output",
                          action="store",
                          default=False,
                          help="path to output file")

    opt_parser.add_option("--random-traffic",
                          action="store",
                          default=False,
                          help="number of random vehicles to generate on the simulation network")

    options, args = opt_parser.parse_args()
    return options


# contains TraCI control loop
def start_server():

    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = SUMO
    else:
        sumoBinary = SUMOGUI

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "--start",
                 "-c", options.config,
                 "--net-file", options.net,
                 "--tripinfo-output", options.output,
                 "--error-log", "errors.txt",
                 "--tripinfo-output.write-unfinished",
                 "--ignore-route-errors", "true",
                 #  "--num-clients", SIMULATION_CLIENTS,
                 "--delay", SIMULATION_DELAY
                #  "--step-length", SIMULATION_STEP_LENGTH
                 ],
                port=PORT)
    traci.setOrder(1)

    if options.schedule != None:
        process_schedule(options.schedule)

    forward_simulation_step()


def find_nearest_edge_to_geocordinates(lon, lat, net: Net):
    radius = 1
    x, y = net.convertLonLat2XY(lon, lat)
    lanes = []

    while radius < MAX_SEARCH_RADIUS:
        lanes = net.getNeighboringLanes(x, y, radius)
        # Could not find any edges within the specified radius. Increase the radius and continue the search.
        if len(lanes) == 0:
            radius += 5
            continue
        else:
            lanes.sort(key=lambda x: x[1])
            for lane, distance in lanes:
                if any(tag in lane._allowed for tag in ALLOWED_VEHICLES):
                    return lane._edge._id
            # Could not find eligible edge. Increase the radius and continue the search.
            radius += 5

    print('There is no eligible edge near the provided geocordinates. No edge supports passing vehicles.')
    raise error('Edge not found within the valid radius.')


def insertVehicle(vehicle_id, departure_address, destination_address, simulation_network: Net):

    departure_lat, departure_lon, departure_display_name = geocode(
        departure_address)

    from_edge = find_nearest_edge_to_geocordinates(
        departure_lon,
        departure_lat,
        simulation_network)

    destination_lat, destination_lon, destination_display_name = geocode(
        destination_address)

    to_edge = find_nearest_edge_to_geocordinates(
        destination_lon,
        destination_lat,
        simulation_network)

    trip_id = f"{from_edge}_{to_edge}"
    vehicle_id = f"service_vehicle_{vehicle_id}"

    traci.route.add(trip_id, [from_edge, to_edge])
    traci.vehicle.add(vehicle_id, trip_id, typeID=SERVICE_VEHICLE_TYPE)
    print(
        f"New Service Vehicle Added. Vehicle_id: {vehicle_id} - from: {departure_address} -> to: {destination_address}")


def process_schedule(schdule_file_path):
    schedule = pd.read_csv(schdule_file_path)
    net = load_simulation_network()

    for index, row in schedule.iterrows():
        try:
            insertVehicle(index, row['from'], row['to'], net)
        except:
            print('Error occured while inserting vehilce.')


def forward_simulation_step():
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        # while True:
        traci.simulationStep()
        step += 1

        process_change_requests()
        # print(f"Current Simulation Time: {traci.simulation.getTime()}")

    traci.close()
    sys.stdout.flush()


def process_change_requests():
    changes = get_changes()
    if len(changes) != 0:
        try:
            for change in changes:
                action = change.action
                match action:
                    case change_types.NEW_DESTINATION:
                        setNewDestination(
                            change.vehicle_id,
                            change.destination)
                    case change_types.NEW_VEHICLE:
                        insertNewVehicle(change.vehicle_id,
                                         change.departure, change.destination)

        except:
            print(f"change command execution failed.")
        finally:
            clear_changes()


def setNewDestination(vehicle_id, address):
    lat, lon, display_name = geocode(address)
    net = load_simulation_network()

    edgeId = find_nearest_edge_to_geocordinates(lon, lat, net)

    traci.vehicle.changeTarget(vehicle_id, f"{edgeId}")
    traci.vehicle.setColor(vehicle_id, (255, 0, 0))
    print(
        f"Rerouted Vehicle: {vehicle_id} to Edge: {edgeId}, address: {address}")


def insertNewVehicle(vehicle_id, departure, destination):
    net = load_simulation_network()
    insertVehicle(vehicle_id, departure, destination, net)


    # main entry point
if __name__ == "__main__":
    start_server()
