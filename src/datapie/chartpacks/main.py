"""
Time series chartpacks
"""


#[

from __future__ import annotations

import functools as _ft
import re as _re
import copy as _cp
import documark as _dm
import plotly.graph_objects as _pg
from collections.abc import Sequence

from .. import descriptions as _descriptions
from .. import ez_plotly as _ez_plotly
from ..periods import Period
from ..databoxes import main as _databoxes

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self, Callable
    from collections.abc import Iterator, Iterable
    from types import EllipsisType

#]


__all__ =  (
    "Chartpack",
)


_FIGURE_SETTINGS = {
    "legend": None,
    "show_legend": None,
    "highlight": None,
    "tiles": None,
    "shared_xaxes": False,
    "figure_height": None,
    "vertical_spacing": None,
}
_FIGURE_SETTINGS_KEYS = tuple(_FIGURE_SETTINGS.keys(), )


_CHART_SETTINGS = {
    "transform": None,
    "transforms": {},
    "reverse_plot_order": False,
    "span": ...,
    "chart_type": "line",
    "update_traces": None,
    "vline": None,
    "round_to": None,
}
_CHART_SETTINGS_KEYS = tuple(_CHART_SETTINGS.keys(), )


_CHART_INPUT_STRING_PATTERN = _re.compile(
    r"^(?:(?P<title>.*?):)?(?P<expression>.*?)(?:\[(?P<transform>.*?)\])?$"
)


@_dm.reference(
    path=("visualization_reporting", "chartpacks.md", ),
    categories={
        "constructor": "Creating new chartpacks",
        "information": "Getting information about chartpacks",
        "property": None,
        "plot": "Plotting chartpacks",
        "add": "Adding figures and charts to chartpacks",
    }
)
class Chartpack(
    _descriptions.Mixin,
):
    r"""
················································································

Chartpacks
===========

A chartpack holds figures, a figure holds charts, and a chart holds one
expression. Nothing is read from any data until `plot` is called, so the
same pack can be plotted against a different databox each time.

Charts are described by strings of the form

    "Title: expression[transform]"

The title and the transform are both optional, so `"gdp"`, `"gdp[pct]"`
and `"Output: gdp"` are all accepted. The expression is handed to
`Databox.evaluate_expression`, so it is not restricted to a series name:
`"gdp/cpi"` divides one series by another.

Settings cascade from the chartpack down to its figures and charts:

| Level | Settings
|-------|----------
| Figure | `legend`, `show_legend`, `highlight`, `tiles`, `shared_xaxes`, `figure_height`, `vertical_spacing`
| Chart | `transform`, `transforms`, `span`, `chart_type`, `update_traces`, `vline`, `round_to`, `reverse_plot_order`

At each level the order of resolution is the explicit keyword, then the
value inherited from the level above, then the module default. Figure
settings always fall back to a default; chart settings do not, and a
chart setting absent from both the call and the cascade is simply left
out of the figure's cascade dictionary.

Keyword arguments matching neither list are accepted by the constructor
and discarded without error.

················································································
    """
    #[


    __slots__ = (
        "title",
        "figures",
        "_figure_settings",
        "_chart_settings",
        "_description",
        "_context",
    )

    def __init__(
        self,
        title: str = "",
        context: dict | None = None,
        **kwargs,
    ) -> None:
        """
        """
        self.title = title
        self.figures = []
        self._description = None
        self._context = context
        #
        self._figure_settings = {
            n: kwargs[n]
            for n in _FIGURE_SETTINGS_KEYS
            if n in kwargs
        }
        #
        self._chart_settings = {
            n: kwargs[n]
            for n in _CHART_SETTINGS_KEYS
            if n in kwargs
        }


    @classmethod
    @_dm.reference(category="constructor", call_name="Chartpack", )
    def _constructor_doc():
        r"""
················································································

## `Chartpack`

==Create a new, empty chartpack.==

    self = Chartpack(
        title="",
        context=None,
        **settings,
    )


**Input arguments.**


???+ input "title"
    Stored on the object and read only by `__repr__`. It is not passed
    to any figure or chart, and does not appear on a plotted figure --
    the caption at the top of a figure comes from the string given to
    `add_figure`.

???+ input "context"
    A dictionary of extra names made available when chart expressions
    are evaluated. It is forwarded through `plot` to
    `Databox.evaluate_expression`.

???+ input "**settings"
    Any of the figure or chart settings listed above, to be inherited by
    the figures and charts added later. Names matching neither list are
    discarded silently.


### Returns


A new `Chartpack` holding no figures.

················································································
        """
        pass


    def copy(self, ) -> Self:
        r"""
················································································

## `Chartpack.copy`

==Create a copy of the chartpack, with its figures and their charts copied too.==

    new = self.copy()

The title, the figure settings, the chart settings and the description
are carried over, and each figure is copied in turn, which copies its
charts.

The `context` is **not** carried over. `copy` builds the new object
through `type(self)()`, which sets `context` to `None`, and never
assigns it afterwards, so a copy evaluates its expressions without
whatever context the original was given.


### Returns


A new `Chartpack`.

················································································
        """
        new = type(self)()
        new.title = self.title
        new.figures = [i.copy() for i in self.figures]
        new._figure_settings = {k: v for k, v in self._figure_settings.items()}
        new._chart_settings = {k: v for k, v in self._chart_settings.items()}
        new._description = self._description
        return new


    def set_span(
        self,
        span: Iterable[Period] | EllipsisType,
    ) -> None:
        r"""
················································································

## `Chartpack.set_span`

==Set the plotting span on every chart in the pack.==

    self.set_span(span)

The span is a chart setting, so this reaches through each figure to its
charts and assigns to each one. Charts added afterwards are unaffected.


**Input arguments.**


???+ input "span"
    The span to assign to every chart.


### Returns


Nothing; the charts are modified in place.

················································································
        """
        for f in self.figures:
            f.set_span(span, )


    def set_highlight(
        self,
        highlight: Iterable[Period] | EllipsisType,
    ) -> None:
        r"""
················································································

## `Chartpack.set_highlight`

==Set the highlighted span on every figure in the pack.==

    self.set_highlight(highlight)

Unlike `set_span`, this is a figure setting and is assigned to the
figures rather than to the charts. Figures added afterwards are
unaffected.


**Input arguments.**


???+ input "highlight"
    The span to highlight, applied to each subplot when the figure is
    plotted.


### Returns


Nothing; the figures are modified in place.

················································································
        """
        for f in self.figures:
            f.highlight = highlight


    def modify_figure_titles(
        self,
        modifier: Callable[[str], str],
    ) -> None:
        r"""
················································································

## `Chartpack.modify_figure_titles`

==Rewrite every figure title through a function of your own.==

    self.modify_figure_titles(modifier)


**Input arguments.**


???+ input "modifier"
    Called once per figure with that figure's current title, and its
    return value becomes the new title. A figure created without a title
    passes `None` to the modifier.


### Returns


Nothing; the figures are modified in place.

················································································
        """
        for f in self.figures:
            f.title = modifier(f.title, )


    def format_figure_titles(self, **kwargs, ) -> None:
        r"""
        """
        for f in self.figures:
            f.title = f.title.format(**kwargs, ) if f.title else f.title

    @_dm.reference(category="plot", )
    def plot(
        self,
        input_db: _databoxes.Databox,
        show_figures: bool = True,
        return_info: bool = False,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
················································································

## `Chartpack.plot`

==Build one plotly figure per figure in the pack, evaluating every chart expression against a databox.==

    self.plot(
        input_db,
        show_figures=True,
        return_info=False,
        **kwargs,
    )

Each figure lays its charts out on a grid of subplots, sized by the
`tiles` setting or worked out from the number of charts. Each chart
evaluates its expression against `input_db`, applies its transform and
draws into its own subplot. Only the first chart of a figure contributes
to the legend.


**Input arguments.**


???+ input "input_db"
    The `Databox` the chart expressions are evaluated against.

???+ input "show_figures"
    Calls `.show()` on each figure once it has been built. `True` when
    left alone.

???+ input "return_info"
    `False` when left alone, which is why the method hands back nothing.

???+ input "**kwargs"
    Accepted by the signature and never read. Anything passed here is
    discarded without error.


### Returns


`None`, unless `return_info=True`, in which case a dictionary whose one
key `"figures"` holds a tuple of the plotly figures. The figures are
built whether or not they are returned or shown.

················································································
        """
        figures = tuple(
            figure.plot(input_db, context=self._context, )
            for figure in self
        )
        if show_figures:
            for f in figures: f.show()
        if return_info:
            return {
                "figures": figures,
            }


    def format_figure_titles(
        self,
        **kwargs,
    ) -> None:
        r"""
················································································

## `Chartpack.format_figure_titles`

==Apply `str.format` to every figure title.==

    self.format_figure_titles(**kwargs)

The name is defined twice in the class body. The second definition
replaces the first, and it is the one that runs: it delegates to each
figure's `format_figure_title`, which calls `self.title.format(...)`
with no check for a missing title, so a figure created without one
raises `AttributeError: 'NoneType' object has no attribute 'format'`.
The first, shadowed definition guarded against that.


**Input arguments.**


???+ input "**kwargs"
    Passed to `str.format` on each figure title.


### Returns


Nothing; the figures are modified in place.

················································································
        """
        for figure in self:
            figure.format_figure_title(**kwargs, )


    @property
    @_dm.reference(category="property", )
    def num_figures(self, ) -> int:
        r"""
················································································

## `Chartpack.num_figures`

==Number of figures in the chartpack, as a read-only property.==

    n = self.num_figures

················································································
        """
        return len(self.figures, ) if self.figures else 0


    def _add_figure(self, figure: _Figure, ) -> None:
        """
        """
        self.figures.append(figure, )

    @_dm.reference(category="add", )
    def add_figure(self, figure_string: str, **kwargs, ) -> None:
        r"""
················································································

## `Chartpack.add_figure`

==Add a figure to the chartpack and return it, so charts can be added to it.==

    figure = self.add_figure(figure_string, **settings)

The figure inherits the chartpack's figure settings and carries the
chartpack's chart settings forward to the charts added to it.

The returned figure also works as a context manager, so
`with self.add_figure("Title") as fig:` is available; `__enter__`
returns the figure and `__exit__` does nothing.


**Input arguments.**


???+ input "figure_string"
    Used verbatim as the figure title, which plotly draws at the top of
    the figure. Not parsed.

???+ input "**settings"
    Figure settings override what the chartpack passed down. Chart
    settings given here are carried to the charts added to this figure.


### Returns


The new figure object. Note that the method is annotated `-> None`
while returning it.

················································································
        """
        new_figure = _Figure.from_string(
            figure_string,
            figure_settings_cascaded=self._figure_settings,
            chart_settings_cascaded=self._chart_settings,
            **kwargs,
        )
        self._add_figure(new_figure, )
        return new_figure


    @staticmethod
    @_dm.reference(category="add", call_name="add_chart", )
    def _add_chart_doc():
        r"""
················································································

## `add_chart`

==Add one chart to a figure, described by a chart string.==

    figure.add_chart(chart_string, **settings)

The chart string is parsed into a title, an expression and a transform;
see the chartpack overview for the form. The chart inherits the chart
settings carried down from the figure.

A `transform` inherited from the figure is **consumed by the first
chart**: the parsing step removes the key from the cascade dictionary it
is handed, and that dictionary is the figure's own, so charts added
afterwards no longer inherit it. A transform written into the chart
string, or passed here as a keyword, is unaffected.

Where a transform comes from more than one place, the chart string wins,
then this call's keyword, then the inherited value.


**Input arguments.**


???+ input "chart_string"
    `"Title: expression[transform]"`, with the title and the transform
    both optional.

???+ input "**settings"
    Chart settings for this chart only.


### Returns


Nothing. Unlike `add_figure`, this does not hand back the object it
creates.

················································································
        """
        pass

    def __str__(self, ) -> str:
        """
        """
        return repr(self, )

    def __repr__(self, ) -> str:
        """
        """
        return _tree_repr(self, )

    def _one_liner(self, ) -> str:
        return f"Chartpack({self.title!r}, )"

    def __getitem__(self, item: str | int, ) -> _Figure:
        """
        """
        if isinstance(item, int, ):
            return self.figures[item]
        if isinstance(item, str, ):
            return next(f for f in self.figures if f.title == item)


    def __iter__(self, ) -> Iterator[_Figure]:
        """
        """
        return iter(self.figures, )


    #]


class _Figure:
    """
    """
    #[

    __slots__ = (
        "title",
        "charts",
        "_chart_settings",
    ) + _FIGURE_SETTINGS_KEYS

    def __init__(
        self,
        title: str | None = None,
    ) -> None:
        """
        """
        for n in self.__slots__:
            setattr(self, n, None, )
        self.title = title
        self.charts = []
        self._chart_settings = {}
        if self.show_legend is None:
            self.show_legend = self.legend is not None and bool(self.legend)

    @classmethod
    def from_string(
        klass,
        figure_title: str,
        figure_settings_cascaded: dict[str, Any] | None = None,
        chart_settings_cascaded: dict[str, Any] | None = None,
        **kwargs,
    ) -> Self:
        """
        """
        self = klass(title=figure_title, )
        figure_settings_cascaded = figure_settings_cascaded or {}
        chart_settings_cascaded = chart_settings_cascaded or {}
        #
        for key in _FIGURE_SETTINGS_KEYS:
            if key in kwargs:
                setattr(self, key, kwargs[key], )
                continue
            if key in figure_settings_cascaded:
                setattr(self, key, figure_settings_cascaded[key], )
                continue
            else:
                setattr(self, key, _FIGURE_SETTINGS[key], )
                continue
        #
        for key in _CHART_SETTINGS_KEYS:
            if key in kwargs:
                self._chart_settings[key] = kwargs[key]
                continue
            if key in chart_settings_cascaded:
                self._chart_settings[key] = chart_settings_cascaded[key]
                continue
        #
        return self

    @property
    def num_charts(self, ) -> int:
        r"""
················································································

## `num_charts`

==Number of charts in the figure, as a read-only property.==

    n = figure.num_charts

················································································
        """
        return len(self.charts, )


    def copy(self, ) -> Self:
        r"""
················································································

## `copy`

==Create a copy of the figure, with its charts copied too.==

    new = figure.copy()

The title, every figure setting and the chart-settings cascade are
carried over, and each chart is copied in turn.


### Returns


A new figure.

················································································
        """
        new = type(self)()
        new.title = self.title
        for n in _FIGURE_SETTINGS_KEYS:
            setattr(new, n, getattr(self, n, None), )
        new.charts = [i.copy() for i in self.charts]
        new._chart_settings = {k: v for k, v in self._chart_settings.items()}
        return new


    def set_span(
        self,
        span: Iterable[Period] | EllipsisType,
    ) -> None:
        r"""
················································································

## `set_span`

==Set the plotting span on every chart in this figure.==

    figure.set_span(span)


**Input arguments.**


???+ input "span"
    The span to assign to each chart already added to this figure.


### Returns


Nothing; the charts are modified in place.

················································································
        """
        for ch in self.charts:
            ch.span = span


    def plot(
        self,
        input_db: _databoxes.Databox,
        context: dict | None = None,
    ) -> _pg.Figure:
        r"""
        """
        tiles = _resolve_tiles(self.tiles, self.num_charts, )
        figure = _ez_plotly.make_subplots(
            rows_columns=(tiles[0], tiles[1], ),
            subplot_titles=tuple(chart.caption for chart in self),
            shared_xaxes=self.shared_xaxes,
            figure_height=self.figure_height,
            vertical_spacing=self.vertical_spacing,
        )
        for i, chart in enumerate(self, ):
            chart.plot(
                input_db, figure, i,
                context=context,
                legend=self.legend,
                include_in_legend=(i == 0),
            )
            if self.highlight is not None:
                _ez_plotly.highlight(figure, self.highlight, subplot=i, )
        #
        figure.update_layout(
            title={"text": self.title, },
            showlegend=self.show_legend,
        )
        #
        return figure

    def format_figure_title(
        self,
        **kwargs,
    ) -> None:
        r"""
················································································

## `format_figure_title`

==Apply `str.format` to this figure's title.==

    figure.format_figure_title(**kwargs)

There is no check for a missing title, so a figure created without one
raises `AttributeError: 'NoneType' object has no attribute 'format'`.


**Input arguments.**


???+ input "**kwargs"
    Passed to `str.format` on the title.


### Returns


Nothing; the title is replaced in place.

················································································
        """
        self.title = self.title.format(**kwargs, )


    def __str__(self, ) -> str:
        """
        """
        return repr(self, )

    def __repr__(self, ) -> str:
        """
        """
        return _tree_repr(self, )

    def _one_liner(self, ) -> str:
        return f"Figure({self.title!r}, )"

    def _add_chart(self, chart: _Chart, ) -> None:
        """
        """
        self.charts.append(chart, )

    def add_charts(self, chart_strings: Iterable[str], **kwargs, ) -> None:
        r"""
················································································

## `add_charts`

==Add several charts to a figure in one call.==

    figure.add_charts(chart_strings, **settings)

Each string is passed to `add_chart` in turn, and the settings apply to
all of them.


**Input arguments.**


???+ input "chart_strings"
    An iterable of chart strings. A bare string is iterated character by
    character, so pass a list or a tuple even for a single chart.

???+ input "**settings"
    Chart settings applied to every chart added by this call.


### Returns


Nothing.

················································································
        """
        for chart_string in chart_strings:
            self.add_chart(chart_string, **kwargs, )


    def add_chart(self, chart_string: str, **kwargs, ) -> None:
        r"""
················································································

## `add_chart`

==Add one chart to a figure, described by a chart string.==

    figure.add_chart(chart_string, **settings)

The chart string is parsed into a title, an expression and a transform;
see the chartpack overview for the form. The chart inherits the chart
settings carried down from the figure.

A `transform` inherited from the figure is **consumed by the first
chart**: the parsing step removes the key from the cascade dictionary it
is handed, and that dictionary is the figure's own, so charts added
afterwards no longer inherit it. A transform written into the chart
string, or passed here as a keyword, is unaffected.

Where a transform comes from more than one place, the chart string wins,
then this call's keyword, then the inherited value.


**Input arguments.**


???+ input "chart_string"
    `"Title: expression[transform]"`, with the title and the transform
    both optional.

???+ input "**settings"
    Chart settings for this chart only.


### Returns


Nothing. Unlike `add_figure`, this does not hand back the object it
creates.

················································································
        """
        chart = _Chart.from_string(
            chart_string,
            chart_settings_cascaded=self._chart_settings,
            **kwargs,
        )
        self._add_chart(chart, )


    def get_chart_input_strings(self, ) -> tuple[str, ...]:
        r"""
················································································

## `get_chart_input_strings`

==Return the chart strings the figure was built from.==

    strings = figure.get_chart_input_strings()

Each chart keeps the string it was parsed from, so this gives back the
specification rather than the parsed parts.


### Returns


A tuple of the original chart strings, in the order the charts were
added.

················································································
        """
        return tuple(c.input_string for c in self.charts)


    def __iter__(self, ) -> Iterator[_Chart]:
        """
        """
        return iter(self.charts, )

    def __enter__(self, ) -> Self:
        return self

    def __exit__(self, *args, **kwargs, ) -> None:
        pass

    #]


class _Chart:
    r"""
    """
    #[

    __slots__ = (
        "title",
        "expression",
        "transform",
        "input_string",
    ) + _CHART_SETTINGS_KEYS

    def __init__(
        self,
        expression: str | None = None,
        title: str | None = None,
        transform: str | Callable | None = None,
        input_string: str | None = None,
        chart_settings_cascaded: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        """
        """
        for n in self.__slots__:
            setattr(self, n, None, )
        self.expression = (expression or "").strip()
        self.title = (title or "").strip()
        self.transform = transform or ""
        if isinstance(transform, str):
            self.transform = self.transform.strip()
        self.input_string = input_string
        #
        chart_settings_cascaded = chart_settings_cascaded or {}
        for key in _CHART_SETTINGS_KEYS:
            if getattr(self, key, None) is not None:
                continue
            elif key in kwargs:
                setattr(self, key, kwargs[key], )
                continue
            elif key in chart_settings_cascaded:
                setattr(self, key, chart_settings_cascaded[key], )
                continue
            else:
                setattr(self, key, _CHART_SETTINGS[key], )
                continue

    @classmethod
    def from_string(
        klass,
        input_string: str,
        chart_settings_cascaded: dict[str, Any] | None = None,
        **kwargs,
    ) -> Self:
        """
        """
        match = _CHART_INPUT_STRING_PATTERN.match(input_string, )
        if not match:
            raise ValueError(f"Invalid input string: {input_string!r}")
        match_dict = match.groupdict()
        # Resolve transform - it can come from three places:
        # 1. directly from the input string
        # 2. from kwargs
        # 3. from the cascaded chart settings
        # The order of precedence is 1, 2, 3
        input_string_transform = match_dict.pop("transform", None)
        kwargs_transform = kwargs.pop("transform", None)
        chart_settings_transform = chart_settings_cascaded.pop("transform", None) if chart_settings_cascaded else None
        transform = input_string_transform or kwargs_transform or chart_settings_transform
        return klass(
            **match_dict,
            transform=transform,
            input_string=input_string,
            chart_settings_cascaded=chart_settings_cascaded,
            **kwargs,
        )

    @property
    def caption(self, ) -> str:
        r"""
················································································

## `caption`

==The text drawn above this chart's subplot.==

    text = chart.caption

The title from the chart string when there is one. Otherwise it is built
from the expression, with the transform appended in brackets -- the
transform's own text when it is a string, or the word `transformed` when
it is a function.


### Returns


The caption string.

················································································
        """
        return self.title if self.title else self._create_autocaption()


    def copy(self, ) -> Self:
        r"""
        """
        new = type(self)(
            expression=self.expression,
            title=self.title,
            transform=self.transform,
            input_string=self.input_string,
        )
        for n in _CHART_SETTINGS_KEYS:
            setattr(new, n, getattr(self, n, None), )
        return new

    def _create_autocaption(self, ) -> str:
        r"""Create an automatic caption based on the expression and transform"""
        transform_string = ""
        if self.transform and callable(self.transform, ):
            transform_string = " [transformed]"
        elif self.transform and isinstance(self.transform, str):
            transform_string = f" [{self.transform}]"
        return f"{self.expression}{transform_string}"

    def plot(
        self,
        input_db: _databoxes.Databox,
        figure: _pg.Figure,
        index: int,
        context: dict | None,
        legend: Iterable[str, ...] | None,
        include_in_legend: bool,
    ) -> None:
        """
        """
        series_to_plot = input_db.evaluate_expression(
            self.expression,
            series_function_context=True,
            context=context,
        )
        series_to_plot = self._apply_transform(series_to_plot, )
        series_to_plot.plot(
            figure=figure,
            subplot=index,
            span=self.span,
            show_figure=False,
            freeze_span=True,
            legend=legend,
            include_in_legend=include_in_legend,
            show_legend=False,
            reverse_plot_order=self.reverse_plot_order,
            chart_type=self.chart_type,
            update_traces=self.update_traces,
            vline=self.vline,
            round_to=self.round_to,
        )

    def _apply_transform(self, x, ):
        """
        """
        if self.transform and isinstance(self.transform, str) and self.transforms and (self.transform in self.transforms):
            func = self.transforms[self.transform]
            return func(x, )
        if self.transform and isinstance(self.transform, str):
            func = eval("lambda x:" + self.transform, )
            return func(x, )
        if self.transform and callable(self.transform, ):
            return self.transform(x, )
        return x

    def __str__(self, ) -> str:
        """
        """
        return repr(self, )

    def __repr__(self, ) -> str:
        """
        """
        return _tree_repr(self, )

    def _one_liner(self, ) -> str:
        return f"Chart({self.title!r}, {self.expression!r}, {self.transform!r}, )"

    def __iter__(self, ) -> Iterable:
        yield from ()

    #]


def _add_strings(
    self,
    input_strings: Iterable[str] | str,
    call: Callable,
    **kwargs,
) -> None:
    """
    """
    #[
    if isinstance(input_strings, str, ):
        input_strings = (input_strings, )
    for s in input_strings:
        call(s, )
    #]


def _resolve_tiles(tiles, num_charts, ) -> tuple[int, int]:
    """
    """
    #[
    if tiles is None:
        return _ez_plotly.auto_tiles(num_charts, )
    if isinstance(tiles, int, ):
        return _ez_plotly.auto_tiles(tiles, )
    if isinstance(tiles, Sequence, ):
        return tiles[:2]
    raise TypeError(f"Invalid tiles: {tiles!r}")
    #]


_TREE_INDENT = "    |"
_TREE_BULLET = "--"


def _tree_repr(self, indent: tuple[str] = (), is_last: bool = False, ) -> str:
    """
    """
    #[
    child_indent = _create_child_indent(indent, is_last, )
    child_repr_func = _ft.partial(_tree_repr, indent=child_indent, )
    child_objects = tuple(c for c in self)
    num_child_objects = len(child_objects)
    child_tree_repr = tuple(
        _tree_repr(
            c, indent=child_indent, is_last=(i+1 == len(child_objects)), )
        for i, c in enumerate(child_objects)
    )
    indent_str = "".join(indent, )
    header = indent_str + (
        _TREE_BULLET if indent_str else "") + self._one_liner()
    return "\n".join((header, *child_tree_repr))
    #]


def _create_child_indent(indent: tuple[str], is_last: bool, ) -> str:
    """
    """
    #[
    if is_last and indent:
        indent = indent[:-1] + (" "*len(_TREE_INDENT), )
    return indent + (_TREE_INDENT, )
    #]

