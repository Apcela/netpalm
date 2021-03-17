import abc

from typing import Dict, Union, List, Set, Tuple

from netpalm.backend.core.utilities.rediz_meta import write_meta_error


def normalize_commands(command: Union[List[str], str]=None, commands: Union[List[str], str]=None) -> List[str]:
    """ensure commands are list of strings.  if both command and commands are given, `commands` takes precedence"""
    if not (command, commands):
        raise ValueError('Must provide command or commands')

    if not commands:
        commands = command

    if isinstance(commands, str):
        commands = [command]

    elif not isinstance(commands, List):
        commands = list(commands)

    return commands


def validate_check(check_definition: Dict, result: Union[Dict, str]) -> Union[str, None]:
    """
    :param check_definition: Dict
    {
      "match_str": ["x", "y", "z"],
      "match_type": "include" | "exclude"
    }
    :param result: str|Dict
    """
    match_type = check_definition["match_type"]
    for match_str in check_definition["match_str"]:
        if match_type == "include" and match_str not in str(result):
            return f"{match_str} not found in {result}"
        if match_type == "exclude" and match_str in str(result):
            return f"{match_str} found in {result}"


def validate_post_check(check_definition: Dict, result: Union[Dict, str]) -> None:
    validation_result = validate_check(check_definition, result)
    if validation_result is not None:
        write_meta_error(f"PostCheck Failed: {validation_result}")


def validate_pre_check(check_definition: Dict, result: Union[Dict, str]) -> None:
    validation_result = validate_check(check_definition, result)
    if validation_result is not None:
        write_meta_error(f"PreCheck Failed: {validation_result}")


class BaseDriver(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def connect(self) -> None:
        """Should either be null-op, or set something like a self.session option that can be closed later"""
        raise NotImplementedError()

    @abc.abstractmethod
    def logout(self) -> None:
        """Should close existing session (or be null-op for drivers that don't require sessions)"""
        raise NotImplementedError()

    @abc.abstractmethod
    def sendcommand(self, *args, **kwargs) -> Dict[str, str]:
        """Mandatory endpoint for sending a command"""
        raise NotImplementedError

    @abc.abstractmethod
    def config(self, *args, **kwargs) -> Dict[str, str]:
        """Mandatory endpoint for sending config changes"""
        raise NotImplementedError

    def __enter__(self) -> "BaseDriver":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def exec_command(self, command: Union[List, str] = None, post_checks: List[Dict] = None, **kwargs) -> Dict:
        assert self.session is not None
        commands = normalize_commands(command)

        post_checks = post_checks if post_checks is not None else []

        if not (commands or post_checks):
            raise ValueError('exec_command requires either `command` or `post_checks`')

        result = {}
        if commands:
            result = self.sendcommand(commands)

        for post_check in post_checks:
            command = post_check["get_config_args"]["command"]
            post_check_result = self.sendcommand([command])
            validate_post_check(post_check, post_check_result)

        return result

    def exec_config(self, config: Union[List, str] = None,
                    enable_mode: bool = False,
                    post_checks: List[Dict] = None,
                    pre_checks: List[Dict] = None, **kwargs) -> Dict:
        assert self.session is not None
        # config = normalize_commands(config)

        post_checks = post_checks if post_checks is not None else []
        pre_checks = pre_checks if pre_checks is not None else []

        for pre_check in pre_checks:
            command = pre_check["get_config_args"]["command"]
            pre_check_result = self.sendcommand([command])
            validate_pre_check(pre_check, pre_check_result)

        # testing for pre_check_ok is unnecessary because validation raises exceptions anyway
        result = self.config(config, enable_mode)
        for post_check in post_checks:
            command = post_check["get_config_args"]["command"]
            post_check_result = self.sendcommand([command])
            validate_post_check(post_check, post_check_result)

        return result
