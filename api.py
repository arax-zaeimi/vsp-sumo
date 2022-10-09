from http.client import OK
import os
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import data_access as data
import json
import osmGet as osm
import components.constants as const
import scenarioFromOSM as traffic_agent
import sumo_runner as sumo_agant
import threading

app = Flask(__name__)
api = Api(app)


class Vehicle(Resource):
    def get(self):
        return 'OK'

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('vehicle_id', type=str,
                            help='vehicle identifier')
        parser.add_argument('destination', type=str,
                            help='Destination Address')
        parser.add_argument('departure', type=str, help='Departure Address')
        parser.add_argument('departure_time', type=int,
                            help='Start Time in Seconds')
        args = parser.parse_args()

        jsonData = json.dumps(args)

        data.add_command('add_vehicle', jsonData)
        return 'Command Queued', 201

    def delete(self):
        parser = reqparse.RequestParser()

        parser.add_argument('vehicle_id', type=str,
                            help='vehicle identifier')
        args = parser.parse_args()

        jsonData = json.dumps(args)

        data.add_command('delete_vehicle', jsonData)

        return 'Command Queued', 200


# Update vehicle destination
class Destination(Resource):
    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('vehicle_id', type=str,
                            help='vehicle identifier')
        parser.add_argument('destination', type=str,
                            help='new destination')

        args = parser.parse_args()

        jsonData = json.dumps(args)

        data.add_command(const.COMMAND_NEW_DESTINATION, jsonData)


class Segment(Resource):
    def get(self):
        return 'OK'

    def post(self):
        self.request_payload = reqparse.request.get_data()
        self.params = json.loads(self.request_payload)

        # data.add_command('new_segment', jsonData)
        data.add_segment(self.params['vehicle_id'], self.params['begin'],
                         self.params['departure'], self.params['destination'])

        return 'OK'

    def delete(self):
        self.request_payload = reqparse.request.get_data()
        self.params = json.loads(self.request_payload)

        data.delete_segment(
            self.params['vehicle_id'], self.params['destination'])

        return 'OK'


class Status(Resource):
    def get(self):
        args = request.args

        # data.add_command('new_segment', jsonData)
        segments = data.get_vehicle_segments(args['vehicle_id'])
        return segments


class Plan(Resource):
    def post(self):

        self.request_payload = reqparse.request.get_data()
        self.params = json.loads(self.request_payload)

        data.import_segments(self.params)

        return 'OK'


class SimulationResult(Resource):
    def get(self):
        return 'OK'


class Boundaries(Resource):
    def post(self):

        self.data = reqparse.request.get_data()
        self.coordinates = json.loads(self.data)

        self.map_path = os.getcwd() + const.MAPS_PATH

        self.coordinates = ",".join(str(x) for x in self.coordinates)

        osm.get(
            ["-b=" + (self.coordinates), "-p", "osm", "-d", self.map_path])

        return 'OK'


class Traffic(Resource):
    def post(self):

        self.data = reqparse.request.get_data()
        self.params = json.loads(self.data)

        self.map_path = os.getcwd() + const.MAPS_PATH + "\\osm_bbox.osm.xml"
        self.traffic_dir = os.getcwd() + const.TRAFFIC_PATH

        traffic_agent.main(["--osm", self.map_path,
                            "--out", self.traffic_dir,
                            "--population", str(self.params['population']),
                            "--density", str(self.params['density'])
                            ])
        return 'OK'


class Simulation(Resource):
    def post(self):

        self.request_payload = reqparse.request.get_data()
        self.params = json.loads(self.request_payload)

        t = threading.Thread(
            name="thread", target=sumo_agant.start_server(self.params))
        t.setDaemon(True)
        t.start()

        return 'OK'


api.add_resource(Vehicle, '/vehicles')
api.add_resource(Boundaries, '/map')
api.add_resource(Traffic, '/traffic')
api.add_resource(Plan, '/plan')
api.add_resource(Destination, '/destination')
api.add_resource(Segment, '/segments')
api.add_resource(Simulation, '/simulation_start')
api.add_resource(SimulationResult, '/results')
api.add_resource(Status, '/status')


def start_api():
    app.run(debug=True)


if __name__ == '__main__':
    start_api()
