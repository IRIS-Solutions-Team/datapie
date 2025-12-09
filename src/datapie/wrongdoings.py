r"""
Handle exceptions and warnings
"""


#[

from __future__ import annotations

# Standard library imports
import warnings as _wa
import os as _os

# Typing imports
from typing import Literal, NoReturn
from collections.abc import Iterable, Callable

#]


_WARN_SKIPS = (_os.path.dirname(__file__), )
HOW = Literal["error", "warning", "silent"]


_PLAIN_PREFIX = ""
_BLANK_LINE = "⏐"
_LIST_PREFIX = "⏐ * "


class Error(Exception, ):
    """
    """
    #[
    def __init__(self, message, ):
        message = _prepare_message(message, )
        super().__init__(message, )
    #]


class Critical(Error, ):
    r"""
    """
    pass


class Warning(UserWarning, ):
    r"""
    """
    pass


def raise_as(
    how: HOW,
    message: str | Iterable[str],
) -> None:
    r"""
    """
    #[
    _RESOLVE_HOW[how](message)
    #]


def _prepare_message(message_in):
    #[
    if isinstance(message_in, str):
        return _PLAIN_PREFIX + message_in
    else:
        message_in = tuple(message_in)
        title = (message_in[0], )
        listing = tuple(_LIST_PREFIX + e for e in message_in[1:])
        message_out = title
        if listing:
            message_out += (_BLANK_LINE, *listing, _BLANK_LINE )
        return ("\n").join(message_out, )
    #]


def _raise_as_error(
    message: str | Iterable[str],
) -> None:
    """
    """
    #[
    raise Error(message, )
    #]


def _raise_as_warning(
    message: str | Iterable[str],
) -> None:
    r"""
    """
    #[
    message = _prepare_message(message, )
    message = "\nWarning: " + message
    try:
        _wa.warn(message, Warning, skip_file_prefixes=_WARN_SKIPS, )
    except TypeError:
        _wa.warn(message, Warning, )
    #]


warn = _raise_as_warning


def _raise_as_silent(
    message: str | Iterable[str],
) -> None:
    """
    """
    #[
    pass
    #]


_RESOLVE_HOW = {
    "error": _raise_as_error,
    "warning": _raise_as_warning,
    "silent": _raise_as_silent,
}


class Stream:
    """
    """
    #[

    def __init__(
        self,
        title: str,
        /,
    ) -> None:
        """
        """
        self.title = (title, )
        self.messages = ()

    def add(
        self,
        message: str,
    ) -> None:
        ...

    def add_from_iterable(
        self,
        messages: Iterable[str],
    ) -> None:
        for message in messages:
            self.add(message, )

    def _raise(self, /, ) -> None:
        ...

    @property
    def final_message(self, /, ) -> tuple[str, ...]:
        return self.title + self.messages

    #]


class CriticalStream(Stream):
    """
    """
    #[

    def add(
        self,
        message: str,
    ) -> NoReturn:
        """
        """
        self.messages += (message, )
        raise Critical(self.final_message, )

    def _raise(self, *args, **kwargs, ) -> None:
        pass

    #]


class ErrorStream(Stream):
    """
    """
    #[

    def add(
        self,
        message: str,
    ) -> None:
        self.messages += (message, )

    def _raise(self, /, ) -> None:
        """
        """
        if self.messages:
            _raise_as_error(self.final_message, )

    #]


class WarningStream(Stream):
    """
    """
    #[

    def add(
        self,
        message: str,
    ) -> None:
        self.messages += (message, )

    def _raise(self, /, ) -> None:
        """
        """
        if self.messages:
            _raise_as_warning(self.final_message, )

    #]


class SilentStream(Stream):
    """
    """
    #[

    def add(self, *args, **kwargs, ) -> None:
        pass

    def _raise(self, *args, **kwargs, ) -> None:
        pass

    #]


STREAM_FACTORY = {
    "critical": CriticalStream,
    "error": ErrorStream,
    "warning": WarningStream,
    "silent": SilentStream,
}


def create_stream(
    kind: str,
    title: str,
    when_no_stream=None,
) -> Stream:
    r"""
    """
    #[
    if kind not in STREAM_FACTORY and when_no_stream:
        kind = when_no_stream
    return STREAM_FACTORY[kind](title, )
    #]

