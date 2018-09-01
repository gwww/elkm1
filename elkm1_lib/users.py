"""Definition of an ElkM1 User"""

import re

from .const import Max, TextDescriptions
from .elements import Element, Elements


class User(Element):
    """Class representing an User"""
    def __init__(self, index, elk):  # pylint: disable=useless-super-delegation
        super().__init__(index, elk)


class Users(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, User, Max.USERS.value)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.USER.value)

    def _got_desc(self, descriptions):
        super()._got_desc(descriptions)
        # Elk returns all user descriptions rather than just configured users
        for user in self.elements:
            if re.match(r'^USER \d\d\d', user.name):
                user.name = user.default_name()
