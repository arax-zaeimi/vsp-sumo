import data_access
import optparse
import os
import sys
import pandas as pd
import sumolib
import traci
import components.constants as const
import json

from pandas import DataFrame
from distutils import util
from distutils.log import error
from sumolib.net import Net
from components.convertaddress import geocodeByNominatim as geocode
# from components.constants import command_types


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
        SIMULATION_NET_CACHE = sumolib.net.readNet(const.DEFAULT_NET_PATH)

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

    opt_parser.add_option("--plan",
                          action="store",
                          default=False,
                          help="plan of service vehicles including their id, departure, and destination")

    options, args = opt_parser.parse_args()
    return options


# contains TraCI control loop
def start_server(params):

    simulation_id = data_access.add_simulation(
        params["begin"],
        params["end"],
        params["ui_enabled"])

    options = get_options()

    # check binary
    if util.strtobool(params["ui_enabled"]):
        sumoBinary = const.SUMOGUI
    else:
        sumoBinary = const.SUMO

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "--start",
                 "-c", const.DEFAULT_SUMO_CONFIG_PATH,
                 "--begin", params["begin"],
                 "--end", params["end"],
                 "--error-log", "errors.txt",
                 "--delay", params["delay"],
                 "--ignore-route-errors", "true"
                 ],
                port=const.PORT)
    traci.setOrder(1)

    store_segments(params['segments'], simulation_id,
                   int(params["begin"]), int(params["end"]))

    execute_simulation_steps(int(params["end"]), simulation_id)


def find_nearest_edge_to_geocordinates(lon, lat, net: Net):
    radius = 1
    x, y = net.convertLonLat2XY(lon, lat)
    lanes = []

    while radius < const.MAX_SEARCH_RADIUS:
        lanes = net.getNeighboringLanes(x, y, radius)
        # Could not find any edges within the specified radius. Increase the radius and continue the search.
        if len(lanes) == 0:
            radius += 5
            continue
        else:
            lanes.sort(key=lambda x: x[1])
            for lane, distance in lanes:
                if any(tag in lane._allowed for tag in const.ALLOWED_VEHICLES):
                    return lane._edge._id
            # Could not find eligible edge. Increase the radius and continue the search.
            radius += 5

    print('There is no eligible edge near the provided geocordinates. No edge supports passing vehicles.')
    raise Exception('Edge not found within the valid radius.')


def insertVehicle(vehicle_id, departure_address, destination_address, simulation_network: Net):

    try:
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

        traci.route.add(trip_id, [from_edge, to_edge])
        traci.vehicle.add(vehicle_id, trip_id,
                          typeID=const.SERVICE_VEHICLE_TYPE)
        print(
            f"New Service Vehicle Added. Vehicle_id: {vehicle_id} - from: {departure_address} -> to: {destination_address}")
    except Exception as e:
        print("Could not add vehicle!")


def validateSegments(segments, simulation_begin, simulation_end):
    if not segments:
        return

    segments = pd.DataFrame(list(segments), columns=[
        'vehicle_id', 'sequence_number', 'begin_time', 'departure', 'destination', 'simulation_id', 'virtual_vehicle_id'])

    groups = segments.groupby('vehicle_id')
    for vehicle_id, group in groups:
        group.sort_values(by='sequence_number',
                          ascending=True, inplace=True)
        sorted_segments = pd.DataFrame(group)

        for index in sorted_segments.index:
            if (sorted_segments.at[index, 'begin_time'] < simulation_begin or sorted_segments.at[index, 'begin_time'] >= simulation_end):
                raise Exception(
                    'segments begin time must be between simulation begin and end times.')

            if (index > 0 and len(sorted_segments.index) > 1):
                if sorted_segments.at[index, 'departure'] != sorted_segments.at[(index - 1), 'destination']:
                    raise Exception(
                        'segments departure and destinations should follow a chained address. Each departure must be the destination of previous segment.')


def store_segments(segments, simulation_id, simulation_begin, simulation_end):

    if not segments:
        return

    try:
        segments = pd.DataFrame(list(segments), columns=[
            'vehicle_id', 'sequence_number', 'begin_time', 'departure', 'destination', 'simulation_id', 'virtual_vehicle_id'])

        groups = segments.groupby('vehicle_id')
        for vehicle_id, group in groups:
            group.sort_values(by='sequence_number',
                              ascending=True, inplace=True)
            sorted_segments = pd.DataFrame(group)

            for index in sorted_segments.index:
                if (sorted_segments.at[index, 'begin_time'] < simulation_begin or sorted_segments.at[index, 'begin_time'] >= simulation_end):
                    raise Exception(
                        'segments begin time must be between simulation begin and end times.')

                if (index > 0):
                    if sorted_segments.at[index, 'departure'] != sorted_segments.at[(index - 1), 'destination']:
                        raise Exception(
                            'segments departure and destinations should follow a chained address. Each departure must be the destination of previous segment.')

                sorted_segments.at[index, 'simulation_id'] = simulation_id
                sorted_segments.at[index,
                                   'virtual_vehicle_id'] = f"sv_{vehicle_id}#{sorted_segments['sequence_number'][index]}"

            data_access.add_segments(simulation_id, sorted_segments)
    except Exception as e:
        print(e)
        return


def process_segments(simulation_id, simulation_step):
    segments = data_access.get_segments(simulation_id, simulation_step)
    if not segments:
        return

    net = load_simulation_network()
    for segment in segments:
        if segment.status != 0:
            continue
        if segment.begin_time != simulation_step:
            continue
        try:
            insertVehicle(segment.virtual_vehicle_id,
                          segment.departure_address, segment.destination_address, net)
        except:
            print('Error occured while inserting vehilce.')
        finally:
            data_access.update_segment(segment.id, 1)


def execute_simulation_steps(end, simulation_id):
    time = traci.simulation.getTime()
    net = load_simulation_network()

    while time < end:
        try:
            traci.simulationStep()
            time = traci.simulation.getTime()

            process_segments(simulation_id, time)

            log_trajectories(simulation_id, time, net)

            process_commands()

        except Exception as e:
            print(e)
            traci.close(wait=False)
            return

    traci.close(wait=False)
    sys.stdout.flush()


def log_trajectories(simulation_id: int, time: int, net: Net):
    segments = data_access.get_segments(simulation_id, time)
    try:
        if segments:
            vehicles = traci.vehicle.getIDList()
            for segment in segments:
                if segment.virtual_vehicle_id in vehicles:
                    position = traci.vehicle.getPosition(
                        segment.virtual_vehicle_id)
                    lon, lat = net.convertXY2LonLat(
                        position[0], position[1])
                    data_access.add_trajectory(
                        simulation_id, segment.virtual_vehicle_id, lat, lon, time)
    except Exception as error:
        print('Could not log trajectories')


def process_commands():
    changes = data_access.get_commands()
    if not changes:
        return
    try:
        for change in changes:
            action = change.command_type
            action_params = json.loads(change.command_body)
            match action:
                case const.COMMAND_NEW_DESTINATION:
                    setNewDestination(
                        action_params['vehicle_id'],
                        action_params['destination'])
                case const.COMMAND_NEW_VEHICLE:
                    insertNewVehicle(action_params['vehicle_id'],
                                     action_params['departure'], action_params['destination'])
                case const.COMMAND_ADD_SEGMENT:
                    addSegment(
                        action_params['vehicle_id'], action_params['departure'], action_params['destination'], action_params['stop'])
                    break
                case const.COMMAND_REMOVE_SEGMENT:
                    removeSegment(action_params['vehicle_id'],
                                  action_params['destination'])
                    break

    except Exception as e:
        print(f"change command execution failed. {e}")
    finally:
        data_access.clear_commands()


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


def addSegment(vehicle_id, begin, departure, destinaiton):
    return


def removeSegment(vehicle_id, destination):
    return


    # main entry point
if __name__ == "__main__":
    start_server()
