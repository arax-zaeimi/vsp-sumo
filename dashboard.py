from __future__ import absolute_import
from __future__ import print_function

from argparse import ArgumentParser
from dashboard.SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import os
import traceback
import webbrowser
import json
import threading
import osmGet
import components.constants as const
import scenarioFromOSM as traffic_agent
import sumo_runner as sumo_agant
import data_access as dal

SUMO_HOME = os.environ.get("SUMO_HOME", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))


class Builder(object):
    prefix = "osm"

    def __init__(self, data, local):
        self.files = {}
        self.files_relative = {}
        self.data = data

        self.tmp = None

        self.tmp = os.getcwd() + const.MAPS_PATH
        self.origDir = os.getcwd()
        print("Building scenario in '%s'" % self.tmp)

    def report(self, message):
        pass

    def filename(self, use, name, usePrefix=True):
        prefix = self.prefix if usePrefix else ''
        self.files_relative[use] = prefix + name
        self.files[use] = os.path.join(self.tmp, prefix + name)

    def downloadMap(self):
        self.filename("osm", const.MAP_FILE_NAME)
        self.filename("net", ".net.xml")
        self.report("Downloading map data")
        osmGet.get(
            ["-b=" + (",".join(map(str, self.data["coords"]))), "-p", self.prefix, "-d", self.tmp])
        self.report("Maps downloaded")
        return


class OSMImporterWebSocket(WebSocket):

    local = False
    outputDir = None

    def report(self, message):
        print(message)
        self.sendMessage(u"report " + message)
        # number of remaining steps
        self.steps -= 1

    def handleMessage(self):
        data = json.loads(self.data)

        data_type = data['type']
        data_body = data['body']

        if data_type == 'set_map':
            thread = threading.Thread(target=self.build, args=(data_body,))
            thread.start()

        elif data_type == 'set_traffic':
            thread = threading.Thread(
                target=self.setTraffic, args=(data_body,))
            thread.start()

        elif data_type == 'start_simulation':

            try:
                sumo_agant.validateSegments(data_body['segments'],
                                            int(data_body["begin"]),
                                            int(data_body["end"]))
            except Exception as e:
                self.report(e.Message)

            self.steps = 1
            self.sendMessage(u"steps %s" % self.steps)

            t = threading.Thread(
                name="thread", target=sumo_agant.start_server(data_body))
            t.setDaemon(True)
            t.start()

        elif data_type == 'add_segment':
            thread = threading.Thread(
                target=self.addSegment, args=(data_body,))
            thread.start()

        elif data_type == 'remove_segment':
            thread = threading.Thread(
                target=self.removeSegment, args=(data_body,))
            thread.start()

        elif data_type == 'change_destination':
            thread = threading.Thread(
                target=self.changeDestination, args=(data_body,))
            thread.start()

    def setTraffic(self, data):
        self.map_path = os.getcwd() + const.MAPS_PATH + "\\osm_bbox.osm.xml"
        self.traffic_dir = os.getcwd() + const.TRAFFIC_PATH

        self.steps = 13
        self.sendMessage(u"steps %s" % self.steps)

        traffic_agent.report = self.report

        traffic_agent.main(["--osm", self.map_path,
                            "--out", self.traffic_dir,
                            "--population", str(data['population']),
                            "--density", str(data['density'])
                            ])

    def build(self, data):
        if self.outputDir is not None:
            data['outputDir'] = self.outputDir
        builder = Builder(data, self.local)
        builder.report = self.report

        self.steps = 2
        self.sendMessage(u"steps %s" % self.steps)

        try:
            builder.downloadMap()
        except Exception:
            print(traceback.format_exc())

            while self.steps > 0:
                self.report("Recovering")
        os.chdir(builder.origDir)

    def addSegment(self, data):
        dal.add_segment(data['vehicle_id'], data['begin'],
                        data['departure'], data['destination'])
        return

    def removeSegment(self, data):
        dal.delete_segment(data['vehicle_id'], data['destination'])
        return

    def changeDestination(data):
        dal.add_command(const.COMMAND_NEW_DESTINATION, data)
        return


parser = ArgumentParser(
    description="VSP Socket Server")

parser.add_argument("--address", default="", help="Address for the Websocket.")
parser.add_argument("--port", type=int, default=8010,
                    help="Port for the Websocket. Please edit script.js when using an other port than 8010.")

if __name__ == "__main__":
    args = parser.parse_args()
    webbrowser.open("file://" + os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "dashboard", "index.html"))
    server = SimpleWebSocketServer(
        args.address, args.port, OSMImporterWebSocket)

    server.serveforever()
