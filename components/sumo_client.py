import optparse
import traci
from components.constants import PORT
from data import get_changes, clear_changes


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


def start_client():

    traci.init(port=PORT)
    traci.setOrder(2)

    # while traci.simulation.getMinExpectedNumber() > 0:
    step = 0
    while True:
        traci.simulationStep()
        step += 1

        changes = get_changes()

        # x, y = traci.vehicle.getPosition('0')
        # lon, lat = traci.simulation.convertGeo(x, y)
        # print(f" {step} : {lat} , {lon}")

        if len(changes) != 0:
            for key in changes:
                traci.vehicle.changeTarget(key, changes[key])
                print(f"Rerouting Vehicle: {key} to Edge: {changes[key]}")
            clear_changes()

        # if step == 30:
        #     traci.vehicle.changeTarget("0", "964696603#0")
        #     print("Vehicle rerouted to its departure")


# main entry point
if __name__ == "__main__":
    start_client()
