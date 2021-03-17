from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from netpalm.backend.plugins.calls.getconfig.exec_command import exec_command
from netpalm.backend.plugins.drivers.puresnmp.puresnmp_drvr import pursnmp

SNMP_ARGS = {
    "type": "get"
}

SNMP_C_ARGS = {
    "host": "1.1.1.1",
    "port": 161,
    "timeout": 2,
    "community": "public",
}


@pytest.fixture()
def rq_job(mocker: MockerFixture) -> MockerFixture:
    mocked_get_current_job = mocker.patch('netpalm.backend.core.utilities.rediz_meta.get_current_job')
    mocked_job = Mock()
    mocked_job.meta = {"errors": []}
    mocked_get_current_job.return_value = mocked_job


@pytest.fixture()
def puresnmp(mocker: MockerFixture) -> MockerFixture:
    mocked = mocker.patch('netpalm.backend.plugins.drivers.puresnmp.puresnmp_drvr.puresnmp', autospec=True)
    return mocked


def test_snmp_driver_creation(puresnmp: Mock):
    snmp_driver = pursnmp(args=SNMP_ARGS, connection_args=SNMP_C_ARGS)
    snmp_driver.connect()


def test_snmp_sendcommand(puresnmp: Mock):
    commands = [
        "0.1.0.1.1.1.1",
        "9.9.9"
    ]
    with pursnmp(args=SNMP_ARGS, connection_args=SNMP_C_ARGS) as snmp_driver:
        result = snmp_driver.sendcommand(command=list(commands))

    puresnmp.get.assert_called()  # make *certain* mock is getting used

    for command in commands:
        puresnmp.get.assert_any_call(ip=SNMP_C_ARGS["host"], community=SNMP_C_ARGS["community"], oid=command,
                                     port=SNMP_C_ARGS["port"], timeout=2)


def test_netmiko_gc_exec_command(puresnmp: Mock):
    commands = [
        "0.1.0.1.1.1.1",
        "9.9.9"
    ]
    ec_kwargs = {
        "library": "puresnmp",
        "command": commands,
        "connection_args": SNMP_C_ARGS
    }
    result = exec_command(**ec_kwargs)

    for command in commands:
        kwargs = {
            'ip': SNMP_C_ARGS['host'],
            'port': SNMP_C_ARGS['port'],
            'community': SNMP_C_ARGS['community'],
            'oid': command,
            'timeout': 2
        }
        puresnmp.get.assert_any_call(**kwargs)
        assert command in result
