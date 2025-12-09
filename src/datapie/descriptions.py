r"""
Description mixin
"""


#[

from __future__ import annotations

from typing import Protocol
import documark as _dm

#]


class HasDescriptionProtocol(Protocol, ):
    r"""
    """
    #[

    _description: str | None = None

    #]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="information", )
    def get_description(
        self: HasDescriptionProtocol,
    ) -> str:
        r"""
................................................................................


==Get description attached to an object==

description = self.get_description()


### Input arguments ###

???+ input "self"
An object from which to get the description.


### Returns ###

???+ returns "description"
The description attached to the object.


................................................................................
        """
        return str(self._description or "")

    @_dm.reference(category="information", )
    def set_description(
            self: HasDescriptionProtocol,
            description: str,
        ) -> None:
        r"""
................................................................................

==Set the description for an object==

self.set_description(
    description,
)


### Input arguments ###

???+ input "self"
An Iris Pie object to which to attach the description.


???+ input "description"
The description to attach to the Iris Pie object.


### Returns ###

This method modifies the Iris Pie object in place and returns `None`.

................................................................................
        """
        self._description = str(description or "")

    #]


__all__ = {}

