from data import insert_new_destination
import optparse


def get_options():

    opt_parser = optparse.OptionParser()

    opt_parser.add_option("-v", "--vehicle",
                          action="store",
                          default=False,
                          help="vehicle_id to reroute")

    opt_parser.add_option("-a", "--address",
                          action="store",
                          default=False,
                          help="valid address in network as new destination")

    opt_parser.add_option("-e", "--edge",
                          action="store",
                          default=False,
                          help="valid edge_id in the network as new destination")

    options, args = opt_parser.parse_args()
    return options


if __name__ == "__main__":
    options = get_options()
    insert_new_destination(options.vehicle, options.address)
