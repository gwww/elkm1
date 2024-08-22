"""
Base of all the elements found on the Elk panel... Zone, Keypad, etc.
"""

from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Callable, Generator
from typing import Any, Generic, TypeVar

from .connection import Connection
from .const import TextDescription, TextDescriptions
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
            # pylint: disable=consider-using-f-string
            "%s:%s" % item  # noqa
            for item in varlist
        )
        return f"{self._index} '{self.name}' {varstr}"

    def as_dict(self) -> dict[str, Any]:
        """Package up the public attributes as a dict."""
        attrs = vars(self)
        return {key: attrs[key] for key in attrs if not key.startswith("_")}

    def _configured_was_set(self) -> None:
        """Called when configured flag is set for an element."""


T = TypeVar("T", bound=Element)


class Elements(Generic[T]):
    """Base for list of elements."""

    def __init__(
        self,
        connection: Connection,
        notifier: Notifier,
        class_: type[T],
        max_elements: int,
    ) -> None:
        self._connection = connection
        self._notifier = notifier
        self.max_elements = max_elements
        self.elements = [class_(i, connection, notifier) for i in range(max_elements)]

        self._text_desc: TextDescription | None = None
        notifier.attach("SD", self._sd_handler)

    def __iter__(self) -> Generator[Element, None, None]:
        yield from self.elements

    def __getitem__(self, key: int) -> Element:
        return self.elements[key]

    def get_descriptions(self, text_desc: TextDescription) -> None:
        """Gets the descriptions for specified type."""
        self._text_desc = text_desc
        self._connection.send(sd_encode(text_desc.desc_type, 0))

    def _sd_handler(
        self, desc_type: int, unit: int, desc: str, show_on_keypad: bool
    ) -> None:
        if not self._text_desc or desc_type != self._text_desc.desc_type:
            return
        if unit < 0 or unit >= self._text_desc.number_descriptions:
            self._text_desc = None
            return

        if desc_type != TextDescriptions.USER.value.desc_type or not re.match(
            r"USER \d\d\d$", desc
        ):
            element = self.elements[unit]
            element.setattr("name", desc, True)
            element._configured = True  # pylint: disable=protected-access
            element._configured_was_set()  # pylint: disable=protected-access
        self._connection.send(sd_encode(desc_type, unit + 1), priority_send=True)

    @abstractmethod
    def sync(self) -> None:
        """Synchronize elements"""
