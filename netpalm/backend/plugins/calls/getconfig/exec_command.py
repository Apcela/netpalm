import logging

from netpalm.backend.core.utilities.rediz_meta import render_netpalm_payload
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from netpalm.backend.plugins.drivers.puresnmp.puresnmp_drvr import pursnmp
from netpalm.backend.plugins.drivers.restconf.restconf import restconf
from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func

log = logging.getLogger(__name__)


def exec_command(**kwargs):
    """main function for executing getconfig commands to southbound drivers"""
    log.debug(f'called w/ {kwargs}')
    lib = kwargs.get("library", False)

    if lib == "netmiko":
        with netmko(**kwargs) as netmiko_driver:
            result = netmiko_driver.exec_command(**kwargs)

    command = kwargs.get("command", False)
    webhook = kwargs.get("webhook", False)
    post_checks = kwargs.get("post_checks", False)

    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command

    if not post_checks:
        try:
            if lib == "netmiko":
                pass

            elif lib == "napalm":
                napl = naplm(**kwargs)
                napl.connect()
                result = napl.sendcommand(commandlst)
                napl.logout()
            elif lib == "puresnmp":
                snm = pursnmp(**kwargs)
                sesh = snm.connect()
                result = snm.sendcommand(sesh, commandlst)
                snm.logout(sesh)
            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.getconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rc = restconf(**kwargs)
                sesh = rc.connect()
                result = rc.sendcommand(sesh)
                rc.logout(sesh)
            else:
                raise NotImplementedError(f"unknown 'library' parameter {lib}")

        except Exception as e:
            write_meta_error(f"{e}")

    else:
        try:
            if lib == "netmiko":
                pass

            elif lib == "napalm":
                napl = naplm(**kwargs)
                napl.connect()
                if commandlst:
                    result = napl.sendcommand(commandlst)
                if post_checks:
                    for postcheck in post_checks:
                        command = postcheck["get_config_args"]["command"]
                        post_check_result = napl.sendcommand([command])
                        for matchstr in postcheck["match_str"]:
                            if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                                write_meta_error(f"PostCheck Failed: {matchstr} not found in {post_check_result}")
                            if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                                write_meta_error(f"PostCheck Failed: {matchstr} found in {post_check_result}")
                napl.logout()

            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.getconfig(sesh)
                ncc.logout(sesh)

            elif lib == "restconf":
                rc = restconf(**kwargs)
                sesh = rc.connect()
                result = rc.sendcommand(sesh)
                rc.logout(sesh)

            else:
                raise NotImplementedError(f"unknown 'library' parameter {lib}")

        except Exception as e:
            write_meta_error(f"{e}")

    try:
        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)

    except Exception as e:
        write_meta_error(f"{e}")

    return result
