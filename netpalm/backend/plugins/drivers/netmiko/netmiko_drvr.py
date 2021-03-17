import logging
from typing import Dict, List

from netmiko import ConnectHandler, BaseConnection

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.base_driver import BaseDriver, normalize_commands

log = logging.getLogger(__name__)


class netmko(BaseDriver):
    def __init__(self, **kwargs):
        self.kwarg = kwargs.get("args", False)
        self.connection_args = kwargs.get("connection_args", False)

    def connect(self) -> BaseConnection:
        try:
            self.session = ConnectHandler(**self.connection_args)
            return self.session

        except Exception as e:
            write_meta_error(f"{e}")

    def sendcommand(self, command: List[str]) -> Dict:
        assert self.session is not None
        session = self.session
        commands = normalize_commands(command)
        try:
            result = {}
            for command in commands:
                if self.kwarg:
                    # normalise the ttp template name for ease of use
                    if "ttp_template" in self.kwarg.keys():
                        if self.kwarg["ttp_template"]:
                            template_name = config.ttp_templates + self.kwarg["ttp_template"] + ".ttp"
                            self.kwarg["ttp_template"] = template_name
                    response = session.send_command(command, **self.kwarg)
                    if response:
                        result[command] = response
                else:
                    response = session.send_command(command)
                    if response:
                        result[command] = response.split("\n")
            return result

        except Exception as e:
            write_meta_error(f"{e}")

    def config(self,
               command='',
               enter_enable=False,
               dry_run=False) -> Dict:
        assert self.session is not None
        session = self.session
        try:
            if type(command) == list:
                comm = command
            else:
                comm = command.splitlines()

            if enter_enable:
                session.enable()

            if self.kwarg:
                response = session.send_config_set(comm, **self.kwarg)
            else:
                response = session.send_config_set(comm)

            if not dry_run:
                # CiscoBaseConnection(BaseConnection)
                # implements commit and save_config in child classes
                if hasattr(session, "commit") and callable(session.commit):
                    try:
                        response += session.commit()
                    except AttributeError:
                        pass
                    except Exception as e:
                        write_meta_error(f"{e}")

                elif hasattr(session, "save_config") and callable(
                        session.save_config):
                    try:
                        response += session.save_config()
                    except AttributeError:
                        pass
                    except Exception as e:
                        write_meta_error(f"{e}")

            result = {}
            result["changes"] = response.split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self) -> None:
        try:
            self.session.disconnect()
        except Exception as e:
            write_meta_error(f"{e}")
