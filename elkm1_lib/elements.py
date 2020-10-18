"""
  Base of all the elements found on the Elk panel... Zone, Keypad, etc.
"""

import re

from abc import abstractmethod
from .message import sd_encode


class Element:
    """Element class"""

    def __init__(self, index, elk):
        self._index = index
        self._elk = elk
        self._callbacks = []
        self.name = self.default_name()
        self._changeset = {}
        self._configured = False

    @property
    def index(self):
        """Get the index, immutable once class created"""
        return self._index

    @property
    def configured(self):
        """If a callback has ever been triggered this will be true."""
        return self._configured

    def add_callback(self, callback):
        """Callbacks when attribute of element changes"""
        self._callbacks.append(callback)

    def remove_callback(self, callback):
        """Callbacks when attribute of element changes"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _call_callbacks(self):
        """Callbacks when attribute of element changes"""
        for callback in self._callbacks:
            callback(self, self._changeset)
        self._changeset = {}

    def setattr(self, attr, new_value, close_the_changeset=True):
        """If attribute value has changed then set it and call the callbacks"""
        existing_value = getattr(self, attr, None)
        if existing_value != new_value:
            setattr(self, attr, new_value)
            self._changeset[attr] = new_value

        if close_the_changeset and self._changeset:
            self._call_callbacks()

    def default_name(self, separator="-"):
        """Return a default name for based on class and index of element"""
        return f"{self.__class__.__name__}{separator}{self._index + 1:03}"

    def is_default_name(self):
        """Check if the name assigned is the default_name"""
        return self.name == self.default_name()

    def __str__(self):
        varlist = {
            k: v
            for (k, v) in vars(self).items()
            if not k.startswith("_") and k != "name"
        }.items()
        varstr = " ".join("%s:%s" % item for item in varlist)
        return "{} '{}' {}".format(self._index, self.name, varstr)

    def as_dict(self):
        """Package up the public attributes as a dict."""
        attrs = vars(self)
        return {key: attrs[key] for key in attrs if not key.startswith("_")}


class Elements:
    """Base for list of elements."""

    def __init__(self, elk, class_, max_elements):
        self.elk = elk
        self.max_elements = max_elements
        self.elements = [class_(i, elk) for i in range(max_elements)]
        self.elk.add_sync_handler(self.sync)

    def __iter__(self):
        for element in self.elements:
            yield element

    def __getitem__(self, key):
        return self.elements[key]

    def _got_desc(self, descriptions):
        from .users import Users

        # Elk reports descriptions for all 199 users, irregardless of how many
        # are configured. Don't set their name and configured flag.
        user_re = re.compile(r"USER \d\d\d") if isinstance(self, Users) else None

        for element in self.elements:
            if element.index >= len(descriptions):
                break
            name = descriptions[element.index]
            if name is not None:
                if user_re and user_re.match(name):
                    continue
                element.setattr("name", name, True)
                element._configured = True

    def get_descriptions(self, description_type):
        """
        Gets the descriptions for specified type.
        When complete the callback is called with a list of descriptions
        """
        (desc_type, max_units) = description_type
        results = [None] * max_units
        self.elk._descriptions_in_progress[desc_type] = (
            max_units,
            results,
            self._got_desc,
        )
        self.elk.send(sd_encode(desc_type=desc_type, unit=0))

    @abstractmethod
    def sync(self):
        """Synchronize elements"""
        pass
