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
    def exec_command(self, **kwargs) -> Dict:
        """Mandatory entrypoint for exec_command call"""
        raise NotImplementedError()

    @abc.abstractmethod
    def exec_config(self, **kwargs) -> Dict:
        """Mandatory entrypoint for exec_config call"""
        raise NotImplementedError()

    def __enter__(self) -> "BaseDriver":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
