"""
  Base of all the elements found on the Elk panel... Zone, Keypad, etc.
"""

from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Generator, Generic, Type, TypeVar

from .connection import Connection
from .const import TextDescriptions
from .message import sd_encode
from .notify import Notifier


class Element:
    """Element class"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        self._index = index
        self._connection = connection
        self._notifier = notifier
        self._observers: list[Callable[[Element, dict[str, Any]], None]] = []
        self.name: str = self.default_name()
        self._changeset: dict[str, Any] = {}
        self._configured: bool = False

    @property
    def index(self) -> int:
        """Get the index, immutable once class created"""
        return self._index

    @property
    def configured(self) -> bool:
        """If a callback has ever been triggered this will be true."""
        return self._configured

    def add_callback(self, observer: Callable[[Element, dict[str, Any]], None]) -> None:
        """Callbacks when attribute of element changes"""
        self._observers.append(observer)

    def remove_callback(
        self, observer: Callable[[Element, dict[str, Any]], None]
    ) -> None:
        """Callbacks when attribute of element changes"""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self) -> None:
        """Callbacks when attribute of element changes"""
        for observer in self._observers:
            observer(self, self._changeset)
        self._changeset = {}

    def setattr(
        self, attr: str, new_value: Any, close_the_changeset: bool = True
    ) -> None:
        """If attribute value has changed then set it and call the callbacks"""
        existing_value: Any = getattr(self, attr, None)
        if existing_value != new_value:
            setattr(self, attr, new_value)
            self._changeset[attr] = new_value

        if close_the_changeset and self._changeset:
            self._notify()

    def default_name(self, separator: str = "-") -> str:
        """Return a default name for based on class and index of element"""
        return f"{self.__class__.__name__}{separator}{self._index + 1:03}"

    def is_default_name(self) -> bool:
        """Check if the name assigned is the default_name"""
        return self.name == self.default_name()

    def __str__(self) -> str:
        varlist = {
            k: v
            for (k, v) in vars(self).items()
            if not k.startswith("_") and k != "name"
        }.items()
        varstr = " ".join(
            "%s:%s" % item  # pylint: disable=consider-using-f-string
            for item in varlist
        )
        return f"{self._index} '{self.name}' {varstr}"

    def as_dict(self) -> dict[str, Any]:
        """Package up the public attributes as a dict."""
        attrs = vars(self)
        return {key: attrs[key] for key in attrs if not key.startswith("_")}


T = TypeVar("T", bound=Element)


class Elements(Generic[T]):
    """Base for list of elements."""

    def __init__(
        self,
        connection: Connection,
        notifier: Notifier,
        class_: Type[T],
        max_elements: int,
    ) -> None:
        self._connection = connection
        self._notifier = notifier
        self.max_elements = max_elements
        self.elements = [class_(i, connection, notifier) for i in range(max_elements)]

        self._get_description_state: tuple[
            int, int, list[str | None], Callable[[list[str | None], int], None]
        ] | None = None
        notifier.attach("SD", self._sd_handler)

    def __iter__(self) -> Generator[Element, None, None]:
        for element in self.elements:
            yield element

    def __getitem__(self, key: int) -> Element:
        return self.elements[key]

    def _sd_handler(
        self, desc_type: int, unit: int, desc: str, show_on_keypad: bool
    ) -> None:
        if not self._get_description_state:
            return
        (_desc_type, count, results, callback) = self._get_description_state
        if desc_type != _desc_type:
            return

        if unit < 0 or unit >= count:
            callback(results, desc_type)
            self._get_description_state = None
        else:
            results[unit] = desc
            self._connection.send(sd_encode(desc_type, unit + 1))

    def _got_desc(self, descriptions: list[str | None], desc_type: int) -> None:
        # Elk reports descriptions for all 199 users, irregardless of how many
        # are configured. Only set configured for those that are really there.
        if desc_type == TextDescriptions.USER.value[0]:
            user_re = re.compile(r"USER \d\d\d")
        else:
            user_re = None

        for element in self.elements:
            if element.index >= len(descriptions):
                break
            name = descriptions[element.index]
            if name is not None:
                if user_re and user_re.match(name):
                    continue
                element.setattr("name", name, True)
                element._configured = True  # pylint: disable=protected-access

    def get_descriptions(self, description_type: tuple[int, int]) -> None:
        """Gets the descriptions for specified type."""
        (desc_type, count) = description_type
        results: list[str | None] = [None] * count
        self._get_description_state = (desc_type, count, results, self._got_desc)
        self._connection.send(sd_encode(desc_type, 0))

    @abstractmethod
    def sync(self) -> None:
        """Synchronize elements"""
