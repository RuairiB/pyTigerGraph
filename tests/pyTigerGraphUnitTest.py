import os
import unittest
from os.path import exists

import pyTigerGraph as pyTG


class pyTigerGraphUnitTest(unittest.TestCase):
    conn = None

    def setUp(self):
        params = {
            "host": "http://127.0.0.1",
            "graphname": "tests",
            "username": "tigergraph",
            "password": "tigergraph",
            "gsqlSecret": "",
            "restppPort": "9000",
            "gsPort": "14240",
            "gsqlVersion": "",
            "userCert": False,
            "certPath": None,
            "sslPort": "443",
            "tgCloud": False,
            "gcp": False
        }

        path = os.path.dirname(os.path.realpath(__file__))
        fname = os.path.join(path, "testserver.cfg")
        if exists(fname):
            try:
                cfg = open(fname, "r")

                lines = cfg.readlines()

                for l in lines:
                    if l.strip()[0] != "#":
                        ll = l.rstrip("\n").split("=")
                        if ll[1]:
                            if ll[1] in ["True", "False"]:
                                params[ll[0]] = ll[1] == "True"
                            else:
                                params[ll[0]] = ll[1]

            except OSError as e:
                print(e.strerror)

        self.conn = pyTG.TigerGraphConnection(host=params["host"], graphname=params["graphname"],
            username=params["username"], password=params["password"], tgCloud=params["tgCloud"],
            restppPort=params["restppPort"], gsPort=params["gsPort"],
            gsqlVersion=params["gsqlVersion"], useCert=params["userCert"],
            certPath=params["certPath"], sslPort=params["sslPort"], gcp=params["gcp"])
        if params.get("getToken", False):
            self.conn.getToken(self.conn.createSecret())
