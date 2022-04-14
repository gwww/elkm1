"""Definition of an ElkM1 Task"""
from time import time

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import tn_encode


class Task(Element):
    """Class representing an Task"""

    def __init__(self, index: int, connection: Connection) -> None:
        super().__init__(index, connection)
        self.last_change = None

    def activate(self) -> None:
        """(Helper) Activate task"""
        self._connection.send(tn_encode(self._index))


class Tasks(Elements):
    """Handling for multiple tasks"""

    def __init__(self, connection: Connection) -> None:
        super().__init__(connection, Task, Max.TASKS.value)
        connection.msg_decode.add_handler("TC", self._tc_handler)

    def sync(self) -> None:
        """Retrieve tasks from ElkM1"""
        self.get_descriptions(TextDescriptions.TASK.value)

    def _tc_handler(self, task: int) -> None:
        self.elements[task].setattr("last_change", time(), True)
