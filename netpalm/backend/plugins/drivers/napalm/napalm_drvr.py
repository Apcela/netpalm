from typing import Dict, List, Union

import napalm
from napalm.base.base import NetworkDriver

from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.base_driver import BaseDriver, normalize_commands


class naplm(BaseDriver):

    def __init__(self, **kwargs):
        self.connection_args = kwargs.get("connection_args", False)
        # convert the netmiko naming format to the native napalm format
        driver_lookup = {"arista_eos": "eos", "juniper": "junos", "cisco_xr": "iosxr", "nxos": "nxos",
                         "cisco_nxos_ssh": "nxos_ssh", "cisco_ios": "ios"}
        self.driver = driver_lookup[self.connection_args.get("device_type", False)]
        self.connection_args["hostname"] = self.connection_args.pop("host")
        del self.connection_args["device_type"]

    def connect(self) -> NetworkDriver:
        try:
            driver = napalm.get_network_driver(self.driver)
            self.session: NetworkDriver = driver(**self.connection_args)
            return self.session
        except Exception as e:
            write_meta_error(f"{e}")

    def sendcommand(self, command=False) -> Dict:
        assert self.session is not None
        session = self.session
        try:
            result = {}
            session.open()
            for c in command:
                if hasattr(session, str(c)):
                    response = getattr(session, str(c))()
                    result[c] = response
                else:
                    response = session.cli([c])
                    result[c] = response[c].split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def exec_command(self, **kwargs) -> Dict:
        raise NotImplementedError()

    def exec_config(self, **kwargs) -> Dict:
        raise NotImplementedError()

    def config(self, command=False, dry_run=False) -> Dict:
        assert self.session is not None
        session = self.session
        try:
            if type(command) == list:
                napalmconfig = ""
                for comm in command:
                    napalmconfig += comm + "\n"
            else:
                napalmconfig = command
            session.open()
            session.load_merge_candidate(config=napalmconfig)
            diff = session.compare_config()
            if dry_run:
                response = session.discard_config()
            else:
                response = session.commit_config()
            result = {}
            result["changes"] = diff.split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self):
        try:
            self.session.close()
        except Exception as e:
            write_meta_error(f"{e}")
