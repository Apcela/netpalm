from netpalm.backend.core.utilities.rediz_meta import write_meta_error, render_netpalm_payload
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from netpalm.backend.plugins.drivers.restconf.restconf import restconf
from netpalm.backend.plugins.utilities.jinja2.j2 import render_j2template
from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func


def exec_config(**kwargs):
    """main function for executing setconfig commands to southbound drivers"""
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf =  kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    pre_checks = kwargs.get("pre_checks", False)
    post_checks = kwargs.get("post_checks", False)
    enable_mode = kwargs.get("enable_mode", False)

    pre_check_ok = True

    if j2conf:
        j2confargs = j2conf.get("args")
        try:
            res = render_j2template(j2conf["template"], template_type="config", kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]

        except Exception as e:
            config = False
            write_meta_error(f"{e}")

    if lib == "netmiko":
        try:
            del kwargs["config"]
        except KeyError:
            pass

        with netmko(config=config, **kwargs) as netmiko_driver:
            result = netmiko_driver.exec_config(config=config, **kwargs)

    if not pre_checks and not post_checks:
        try:
            if lib == "netmiko":
                pass

            elif lib == "napalm":
                napl = naplm(**kwargs)
                napl.connect()
                result = napl.config(config)
                napl.logout()
            elif lib == "ncclient":
                # if we rendered j2config, add it to the kwargs['args'] dict
                if j2conf and config:
                    if not kwargs.get('args', False):
                        kwargs['args'] = {}
                    kwargs['args']['config'] = config
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.editconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rcc = restconf(**kwargs)
                sesh = rcc.connect()
                result = rcc.config(sesh)
                rcc.logout(sesh)
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
                if pre_checks:
                    for precheck in pre_checks:
                        command = precheck["get_config_args"]["command"]
                        pre_check_result = napl.sendcommand([command])
                        for matchstr in precheck["match_str"]:
                            if precheck["match_type"] == "include" and matchstr not in str(pre_check_result):
                                write_meta_error(f"PreCheck Failed: {matchstr} not found in {pre_check_result}")
                                pre_check_ok = False
                            if precheck["match_type"] == "exclude" and matchstr in str(pre_check_result):
                                write_meta_error(f"PreCheck Failed: {matchstr} found in {pre_check_result}")
                                pre_check_ok = False

                if pre_check_ok:
                    result = napl.config(config)
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
                result = ncc.editconfig(sesh)
                ncc.logout(sesh)

            elif lib == "restconf":
                rcc = restconf(**kwargs)
                sesh = rcc.connect()
                result = rcc.config(sesh)
                rcc.logout(sesh)
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
