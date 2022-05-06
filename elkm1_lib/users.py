"""Definition of an ElkM1 User"""

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .notify import Notifier


class User(Element):
    """Class representing an User"""


class Users(Elements[User]):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, User, Max.USERS.value)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.USER.value)

    def username(self, user_number: int) -> str:
        """Return name of user."""
        if 0 <= user_number < self.max_elements:
            return self.elements[user_number].name
        if user_number == 201:
            return "*Program*"
        if user_number == 202:
            return "*Elk RP*"
        if user_number == 203:
            return "*Quick arm*"
        return ""
