from data import insert_new_vehicle
import optparse


def get_options():

    opt_parser = optparse.OptionParser()

    opt_parser.add_option("-v", "--vehicle",
                          action="store",
                          default=False,
                          help="vehicle_id to add")

    opt_parser.add_option("-f", "--departure",
                          action="store",
                          default=False,
                          help="valid departure address")

    opt_parser.add_option("-t", "--destination",
                          action="store",
                          default=False,
                          help="valid destination address")

    options, args = opt_parser.parse_args()
    return options


if __name__ == "__main__":
    options = get_options()
    insert_new_vehicle(options.vehicle, options.departure, options.destination)
