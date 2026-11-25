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
==Get the object's description==

#### Syntax

    description = object.get_description()

#### Input arguments

!!! input "object"

    The object whose description is requested.

#### Returns

!!! returns "description"

    The description as a string, or an empty string if none has been set.
        """
        return str(self._description or "")

    @_dm.reference(category="information", )
    def set_description(
            self: HasDescriptionProtocol,
            description: str | None,
        ) -> None:
        r"""
==Set the object's description==

#### Syntax

    object.set_description(
        description,
    )

#### Input arguments

!!! input "object"

    The object whose description is to be updated.

!!! input "description"

    The new description. An empty value clears the description.

#### Returns

!!! returns "None"

    Updates the description in place.
        """
        self._description = str(description or "")

    #]


__all__ = {}

