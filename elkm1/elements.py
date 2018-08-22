"""
  Base of all the elements found on the Elk panel... Zone, Keypad, etc.
"""

from abc import abstractmethod
from .util import add_sync_handler, get_descriptions


class Element:
    """Element class"""
    def __init__(self, index, elk):
        self._index = index
        self._elk = elk
        self._callbacks = []
        self.name = self.default_name()

    @property
    def index(self):
        """Get the index, immutable once class created"""
        return self._index

    def add_callback(self, callback):
        """Callbacks when attribute of element changes"""
        self._callbacks.append(callback)

    def remove_callback(self, callback):
        """Callbacks when attribute of element changes"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _call_callbacks(self, changed_attribute, new_value):
        """Callbacks when attribute of element changes"""
        for callback in self._callbacks:
            callback(self, changed_attribute, new_value)

    def setattr(self, attr, new_value):
        """If attribute value has changed then set it and call the callbacks"""
        existing_value = getattr(self, attr, None)
        if existing_value == new_value:
            return
        setattr(self, attr, new_value)
        self._call_callbacks(attr, new_value)

    def default_name(self, separator='-'):
        """Return a default name for based on class and index of element"""
        return self.__class__.__name__ + '{}{:03d}'.format(separator, self._index+1)

    def is_default_name(self):
        """Check if the name assigned is the default_name"""
        return self.name == self.default_name()

    def __str__(self):
        varlist = {k:v for (k, v) in vars(self).items() \
           if not k.startswith('_') and k != 'name'}.items()
        varstr = ' '.join("%s:%s" % item for item in varlist)
        return "{} '{}' {}".format(self._index, self.name, varstr)

    def as_dict(self):
        """Package up the attributes as a dict."""
        cdict = self.__dict__.copy()
        del cdict['_elk']
        del cdict['_callbacks']
        return cdict

class Elements:
    """Base for list of elements."""
    def __init__(self, elk, class_, max_elements):
        self.elk = elk
        self.max_elements = max_elements
        self.elements = [class_(i, elk) for i in range(max_elements)]
        add_sync_handler(self.sync)

    def __iter__(self):
        for element in self.elements:
            yield element

    def __getitem__(self, key):
        return self.elements[key]

    def _got_desc(self, descriptions):
        for element in self.elements:
            if element.index >= len(descriptions):
                break
            if descriptions[element.index] is not None:
                element.setattr('name', descriptions[element.index])

    def get_descriptions(self, description_type):
        """Get the list of descriptions for the element."""
        get_descriptions(self.elk, description_type, self._got_desc)

    @abstractmethod
    def sync(self):
        """Synchronize elements"""
        pass
