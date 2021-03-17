from typing import List, Union, Dict

from puresnmp import puresnmp

from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.base_driver import BaseDriver


class pursnmp(BaseDriver):

    def __init__(self, **kwargs):
        self.session = True  # so exec_command, etc don't freak out
        self.connection_args = kwargs.get("connection_args", False)
        if "port" not in self.connection_args.keys():
            self.connection_args["port"] = 161

        if "timeout" not in self.connection_args.keys():
            self.connection_args["timeout"] = 2

        self.input_args = kwargs.get("args", {})
        if "type" not in self.input_args:
            self.input_args["type"] = "get"

    def connect(self):
        """SNMP is connectionless"""
        return True

    def sendcommand(self, command: List[str]):
        try:
            result = {}
            method_type = self.input_args["type"]

            for c in command:
                # remove timeout weirdness for tables
                if method_type == "table":
                    response = getattr(puresnmp, method_type)(
                        ip=self.connection_args["host"],
                        community=self.connection_args["community"],
                        oid=c,
                        port=self.connection_args["port"]
                    )
                else:
                    response = getattr(puresnmp, method_type)(
                        ip=self.connection_args["host"],
                        community=self.connection_args["community"],
                        oid=c,
                        port=self.connection_args["port"],
                        timeout=self.connection_args["timeout"],
                    )

                # render result data for get call
                if method_type == "get":
                    if isinstance(response, bytes):
                        response = response.decode(errors="ignore")
                    result[c] = response

                # render result data for walk call
                elif method_type == "walk":
                    result[c] = []
                    for row in response:
                        oid = str(row[0])
                        oid_raw = row[1]
                        if isinstance(oid_raw, bytes):
                            oid_raw = oid_raw.decode(errors="ignore")
                        result[c].append({oid: oid_raw})

                # render result data for table call
                elif method_type == "table":
                    result[c] = []
                    for key in response[0]:
                        oid = str(key)
                        oid_raw = response[0][key]
                        if isinstance(response[0][key], bytes):
                            oid_raw = oid_raw.decode(errors="ignore")
                        result[c].append({oid: oid_raw})

                else:
                    result[c] = f"{response}"
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def config(self, command=False, dry_run=False):
        return True

    def logout(self):
        return True

    def exec_config(self, config: Union[List, str] = None,
                    enable_mode: bool = False,
                    post_checks: List[Dict] = None,
                    pre_checks: List[Dict] = None, **kwargs) -> Dict:
        raise NotImplementedError("puresnamp driver doesn't implement config changes")
