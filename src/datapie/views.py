"""
Mixin methods for displaying data management objects
"""


#[

from __future__ import annotations

#]


_REPEAT_SHORT_ROW = 2
_VERTICAL_ELLIPSIS = "⋮"
_SHORT_ROWS_ = 5


#---------------------------------------------------------------------------------
# Mixin methods
#---------------------------------------------------------------------------------


class Mixin:
    #[

    def _get_first_line_view(self, ):
        raise NotImplementedError()

    def _get_header_separator(self, ):
        raise NotImplementedError()

    def _get_content_view(self, ):
        raise NotImplementedError()

    def _get_max_key_repr_len_(self, ):
        raise NotImplementedError()

    def _get_short_row_(self, ):
        raise NotImplementedError()

    def _get_header_view_(self, ):
        r"""
        """
        return (
            "", 
            self._get_first_line_view(),
            f"Description: \"{self.get_description()}\"",
            self._get_header_separator(),
        )

    def _get_footer_view_(self, ):
        return ("", )

    def _get_view(self, ):
        r"""
        """
        header_view = self._get_header_view_()
        content_view = self._get_content_view()
        footer_view = self._get_footer_view_()
        return header_view + content_view + footer_view

    def __invert__(self):
        r"""
        ~self for short view
        """
        header_view = self._get_header_view_()
        content_view = self._get_content_view()
        if len(content_view) > 2*_SHORT_ROWS:
            content_view = (
                content_view[:_SHORT_ROWS]
                + (self._get_short_row_(), )*_REPEAT_SHORT_ROW
                + content_view[-_SHORT_ROWS:]
            )
        print("\n".join(header_view + content_view))

    def __repr__(self, ):
        r"""
        """
        return "\n".join(self._get_view())

    def __str__(self, ):
        r"""
        """
        return repr(self)

    #]

#---------------------------------------------------------------------------------

