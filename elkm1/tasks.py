"""Definition of an ElkM1 Task"""
from .const import Max, TextDescriptions
from .elements import Element, Elements


class Task(Element):
    """Class representing an Task"""

    def __init__(self, index): # pylint: disable=useless-super-delegation
        super().__init__(index)

class Tasks(Elements):
    """Handling for multiple tasks"""
    def __init__(self, elk):
        super().__init__(elk, Task, Max.TASKS.value)

    def sync(self):
        """Retrieve tasks from ElkM1"""
        self.get_descriptions(TextDescriptions.TASK.value)
