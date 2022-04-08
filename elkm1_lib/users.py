"""Definition of an ElkM1 User"""

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .elk import Elk


class User(Element):
    """Class representing an User"""

    def __init__(
        self, index: int, elk: Elk
    ) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(index, elk)


class Users(Elements):
    """Handling for multiple areas"""

    def __init__(self, elk: Elk) -> None:
        super().__init__(elk, User, Max.USERS.value)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.USER.value)
