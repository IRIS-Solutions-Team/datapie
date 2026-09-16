r"""
Plotly interface to time series objects
"""


#[

from __future__ import annotations

import os as _os
import json as _js
import copy as _cp
import plotly.graph_objects as _pg
import plotly.io as _pi
import itertools as _it
import functools as _ft
import warnings as _wa
import datetime as _dt

from ..periods import Period
from .. import periods as _periods
from .. import ez_plotly as _ez_plotly
from ..ez_plotly import styles as _plotly_style

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self, Sequence, Iterable, Any, Callable, Literal
    from numbers import Real
    from types import EllipsisType
    from . import Series
    from ..ez_plotly import PlotlyDateAxisModeType

#]


_PLOTLY_STYLES_FOLDER = _os.path.join(_os.path.dirname(__file__), "plotly_styles")
_PLOTLY_STYLES = {
    "layouts": {},
}

with open(_os.path.join(_PLOTLY_STYLES_FOLDER, "plain_layout.json", ), "rt", ) as fid:
    _PLOTLY_STYLES["layouts"]["plain"] = _js.load(fid, )


__all__ = ()



def _line_constructor(style, **kwargs, ):
    default = {"mode": "lines+markers", }
    return _pg.Scatter(
        line_color=style[0],
        line_dash=style[1],
        **(default | kwargs),
    )


def _bar_constructor(style, **kwargs, ):
    return _pg.Bar(
        marker_color=style[0],
        **kwargs,
    )


def _area_constructor(style, **kwargs, ):
    default = {"mode": "lines+markers", }
    return _pg.Scatter(
        line_color=style[0],
        line_dash=style[1],
        fill="tozeroy",
        **(default | kwargs),
    )


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    def plot(
        self,
        chart_type: Literal["line", "bar", "bar_group", "bar_stack", "bar_relative", "bar_overlay", "area"] = "line",
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot`

==Draws the series as a chart of the kind named by `chart_type`, handing the work to the matching `plot_*` method.==

    self.plot(chart_type="line", **kwargs)


**Input arguments.**


???+ input "chart_type"
    Which chart to draw: `"line"`, `"bar"`, `"bar_group"`,
    `"bar_stack"`, `"bar_relative"`, `"bar_overlay"`, `"area"` or
    `"histogram"`. `"line"` when left alone. An unrecognised name
    raises `ValueError`.

???+ input "**kwargs"
    Passed straight on to the chosen `plot_*` method. See `plot_line`
    for the arguments they share.


### Returns


Whatever the chosen method returns, which is `None` unless you pass
`return_info=True`.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> info = x.plot("bar", show_figure=False, return_info=True)
    >>> info["traces"][0].type
    'bar'

································································
        """
        if chart_type == "line":
            trace_constructor=_line_constructor,
            return self.plot_line(**kwargs, )
        elif chart_type in "bar":
            return self.plot_bar(**kwargs, )
        elif chart_type in "bar_group":
            return self.plot_bar_group(**kwargs, )
        elif chart_type == "bar_stack":
            return self.plot_bar_stack(**kwargs, )
        elif chart_type == "bar_overlay":
            return self.plot_bar_overlay(**kwargs, )
        elif chart_type == "bar_relative":
            return self.plot_bar_relative(**kwargs, )
        elif chart_type == "area":
            return self.plot_area(**kwargs, )
        elif chart_type == "histogram":
            return self.plot_histogram(**kwargs, )
        else:
            raise ValueError(f"Invalid chart_type: {chart_type!r}, must be one of 'line', 'bar', 'bar_group', 'bar_stack', 'bar_relative', 'bar_overlay', 'area' or 'histogram'")


    def plot_line(
        self,
        span: Iterable[Period] | EllipsisType = ...,
        update_traces: Iterable[dict] | dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot_line`

==Draws each variant of the series as a line with markers.==

    self.plot_line(span=..., update_traces=None, **kwargs)

The arguments described here are shared with `plot_area`, `plot_bar`
and `plot_histogram`, which differ only in the shape they draw.


**Input arguments.**


???+ input "span"
    The stretch of periods to draw. Left alone it is the span the
    series covers.

???+ input "update_traces"
    Plotly trace settings applied to every trace, given as one
    dictionary, or as an iterable of dictionaries cycled over the
    variants. Nothing is applied when left as `None`.

???+ input "**kwargs"
    Everything else reaches the layout builder. The two that matter most
    are `show_figure`, which is `True` and displays the chart as soon
    as it is built, and `return_info`, which is `False` and is why the
    method hands back nothing. Others include `figure` and `subplot`
    for drawing into an existing figure, `figure_title` and
    `subplot_title`, `legend`, `update_layout`, `highlight`, `vline`
    and `round_to`.


### Returns


`None`, unless `return_info=True`, in which case a dictionary with
`"figure"` and `"traces"`.


### Examples


Nothing comes back until you ask for it:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> x.plot_line(show_figure=False) is None
    True
    >>> info = x.plot_line(show_figure=False, return_info=True)
    >>> sorted(info)
    ['figure', 'traces']

································································
        """
        generate_traces = _ft.partial(
            _generate_plain_traces,
            trace_constructor=_line_constructor,
            series=self,
            update_traces=update_traces,
        )
        periods = self.resolve_periods(span, )
        info, *_, = _create_layout(
            generate_traces=generate_traces,
            periods=periods,
            **kwargs,
        )
        return info


    def plot_bands(
        self,
        span: Iterable[Period] | EllipsisType = ...,
        base_color: str | tuple | None = None,
        shading_weights: Iterable[float] | None = None,
        shading_background: str | tuple | None = None,
        update_band_traces: Iterable[dict] | dict | None = None,
        update_midline_trace: dict | None = None,
        update_layout: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot_bands`

==Draws the variants of the series as shaded bands around a middle line, the way a fan chart shows a forecast.==

    self.plot_bands(
        span=...,
        base_color=None,
        shading_weights=None,
        shading_background=None,
        update_band_traces=None,
        update_midline_trace=None,
        update_layout=None,
        **kwargs,
    )

The variants are paired from the outside in: the first with the last,
the second with the second from last, and so on, each pair becoming one
filled band. An odd number of variants leaves the middle one over, and
it is drawn as a plain line. So six variants give three bands, and
seven give three bands and a midline.


**Input arguments.**


???+ input "base_color"
    The colour the bands are shaded from. Left as `None` it is the next
    colour in the figure's style cycle.

???+ input "shading_weights"
    How the shades step from the outer band to the inner. The default
    shading is used when left as `None`.

???+ input "shading_background"
    The colour the shades are blended towards. The default shading is
    used when left as `None`.

???+ input "update_band_traces"
    Plotly settings applied to the band traces, as one dictionary or an
    iterable cycled over the bands.

???+ input "update_midline_trace"
    Plotly settings applied to the middle line, when there is one.

???+ input "update_layout"
    Plotly layout settings. **A non-empty dictionary passed here is
    modified in place:** a `legend_traceorder` key is added to it, so
    the dictionary you still hold comes back with an extra entry. An
    empty one is not, because `update_layout or {}` replaces a falsy
    value with a fresh dictionary before the key is set.

???+ input "span, **kwargs"
    As described under `plot_line`.


### Returns


`None`, unless `return_info=True`, in which case a dictionary with
`"figure"` and `"traces"`.


### Examples


Three variants make one band and one midline:

    >>> import numpy as np
    >>> import datapie as dp
    >>> b = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.column_stack([[1., 2.], [3., 4.], [5., 6.]]))
    >>> info = b.plot_bands(show_figure=False, return_info=True)
    >>> len(info["traces"])
    2

································································
        """
        generate_traces = _ft.partial(
            _generate_band_traces,
            series=self,
            base_color=base_color,
            shading_weights=shading_weights,
            shading_background=shading_background,
            update_band_traces=update_band_traces,
            update_midline_trace=update_midline_trace,
        )
        periods = self.resolve_periods(span, )
        update_layout = update_layout or {}
        update_layout.setdefault("legend_traceorder", "reversed")
        info, *_, = _create_layout(
            generate_traces=generate_traces,
            periods=periods,
            update_layout=update_layout,
            legend_order="reversed",
            **kwargs,
        )
        return info


    def plot_area(
        self,
        span: Iterable[Period] | EllipsisType = ...,
        update_traces: Iterable[dict] | dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot_area`

==Draws each variant of the series as a line with the space down to zero filled in.==

    self.plot_area(span=..., update_traces=None, **kwargs)

The same as `plot_line` apart from the fill, and all its arguments are
described there.


**Input arguments.**


???+ input "span, update_traces, **kwargs"
    As described under `plot_line`.


### Returns


`None`, unless `return_info=True`, in which case a dictionary with
`"figure"` and `"traces"`.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> info = x.plot_area(show_figure=False, return_info=True)
    >>> info["traces"][0].fill
    'tozeroy'

································································
        """
        generate_traces = _ft.partial(
            _generate_plain_traces,
            trace_constructor=_area_constructor,
            series=self,
            update_traces=update_traces,
        )
        #
        periods = self.resolve_periods(span, )
        info, *_, = _create_layout(
            generate_traces=generate_traces,
            periods=periods,
            **kwargs,
        )
        return info


    def plot_bar(
        self,
        span: Iterable[Period] | EllipsisType = ...,
        update_traces: Iterable[dict] | dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot_bar`

==Draws each variant of the series as bars.==

    self.plot_bar(span=..., update_traces=None, **kwargs)

The same as `plot_line` apart from the shape, and all its arguments are
described there.

How the bars of several variants sit against each other is set by
`bar_mode`, passed here directly. Four ready-made versions exist, each
being this call with `bar_mode` already fixed:

| Method | `bar_mode` | Effect
|--------|------------|--------
| `plot_bar_stack`    | `"stack"`    | Piles the variants up
| `plot_bar_group`    | `"group"`    | Stands them side by side
| `plot_bar_overlay`  | `"overlay"`  | Draws them on top of one another
| `plot_bar_relative` | `"relative"` | Stacks positive and negative values on opposite sides of the axis

All four take `plot_bar`'s arguments and return what it returns.


**Input arguments.**


???+ input "bar_mode"
    `"stack"`, `"group"`, `"overlay"` or `"relative"`, reaching the
    layout builder through `**kwargs`. Leaving it out sets no bar mode
    at all.

???+ input "span, update_traces, **kwargs"
    As described under `plot_line`.


### Returns


`None`, unless `return_info=True`, in which case a dictionary with
`"figure"` and `"traces"`.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> info = x.plot_bar(bar_mode="group", show_figure=False,
    ...     return_info=True)
    >>> info["figure"].layout.barmode
    'group'

The ready-made version fixes it for you:

    >>> info = x.plot_bar_stack(show_figure=False, return_info=True)
    >>> info["figure"].layout.barmode
    'stack'

································································
        """
        generate_traces = _ft.partial(
            _generate_plain_traces,
            trace_constructor=_bar_constructor,
            series=self,
            update_traces=update_traces,
        )
        #
        periods = self.resolve_periods(span, )
        info, *_ = _create_layout(
            generate_traces=generate_traces,
            periods=periods,
            **kwargs,
        )
        return info


    plot_bar_stack = _ft.partialmethod(plot_bar, bar_mode="stack", )
    plot_bar_group = _ft.partialmethod(plot_bar, bar_mode="group", )
    plot_bar_overlay = _ft.partialmethod(plot_bar, bar_mode="overlay", )
    plot_bar_relative = _ft.partialmethod(plot_bar, bar_mode="relative", )


    def plot_histogram(
        self,
        span: Iterable[Period] | EllipsisType = ...,
        hist_norm: Literal["", "probability", "percent", "density", "probability density"] = "",
        update_traces: Iterable[dict] | dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        r"""
································································

## `Series.plot_histogram`

==Draws the distribution of each variant's values as a histogram.==

    self.plot_histogram(
        span=...,
        hist_norm="",
        update_traces=None,
        **kwargs,
    )

Unlike the other methods here, time does not appear on the chart: the
observations are counted into bins, and `span` only decides which of
them are counted.


**Input arguments.**


???+ input "hist_norm"
    What the bars measure: `""`, `"probability"`, `"percent"`,
    `"density"` or `"probability density"`. Left alone it is `""`,
    which counts observations.

???+ input "span, update_traces, **kwargs"
    As described under `plot_line`.


### Returns


`None`, unless `return_info=True`, in which case a dictionary with
`"figure"` and `"traces"`.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> info = x.plot_histogram(show_figure=False, return_info=True)
    >>> info["traces"][0].type
    'histogram'

································································
        """
        generate_traces = _ft.partial(
            _generate_histogram_traces,
            series=self,
            hist_norm=hist_norm,
            update_traces=update_traces,
        )
        #
        periods = self.resolve_periods(span, )
        info, *_, = _create_layout(
            generate_traces=generate_traces,
            periods=periods,
            xaxis_type="linear",
            freeze_span=False,
            **kwargs,
        )
        return info


    #]


#-------------------------------------------------------------------------------


def _create_layout(
    generate_traces: Callable,
    periods: Iterable[Period],
    #
    xaxis_type: str | None = None,
    figure: _pg.Figure | None = None,
    figure_title: str | None = None,
    subplot_title: str | None = None,
    legend: str | Iterable[str] | None = None,
    legend_order: Literal["normal", "reversed"] | None = None,
    show_figure: bool = True,
    show_legend: bool | None = None,
    include_in_legend: bool | Iterable[bool] = True,
    renderer: str | None = None,
    subplot: tuple[int, int] | int | None = None,
    xline: Iterable[Period|int] | None = None,
    vline: Iterable[Period|int] | None = None,
    highlight: Iterable[Period] | None = None,
    date_axis_mode: PlotlyDateAxisModeType = "period",
    date_format_style: str | dict[int, str] | None = None,
    #
    bar_mode: Literal["stack", "group", "overlay", "relative"] | None = None,
    bar_norm: Literal["fraction", "percent"] | None = None,
    #
    update_layout: dict[str, Any] | None = None,
    #
    freeze_span: bool = False,
    reverse_plot_order: bool = False,
    #
    round_to: int | None = None,
    #
    return_info: bool = False,
) -> dict[str, Any] | None:
    r"""
    """
    #[

    # if type is not None:
    #     _wa.warn("Use 'chart_type' instead of the deprecated 'type'", )
    #     chart_type = type if chart_type is None else chart_type

    # Time span, frequency, date format
    from_until = (periods[0], periods[-1], )
    frequency = periods[0].frequency
    date_format = _ez_plotly.resolve_date_format(date_format_style, frequency, )

    if figure is None:
        figure = _pg.Figure()

    if show_legend is None:
        show_legend = legend is not None

    # Subplot resolution
    row_column, subplot_index, = _ez_plotly.resolve_subplot_reference(figure, subplot, )

    transform = _create_transform_function(round_to=round_to, )

    trace_periods = tuple(
        i.to_plotly_date(mode=date_axis_mode, )
        for i in _periods.periods_from_until(*from_until, )
    )

    style_cycle = _ez_plotly.create_style_cycle(
        figure,
        subplot_index,
        _plotly_style.get_color_order(),
        _plotly_style.get_dash_order(),
    )

    if isinstance(legend, str):
        legend = (legend, )

    traces_iterable = generate_traces(
        style_cycle=style_cycle,
        from_until=from_until,
        trace_periods=trace_periods,
        transform=transform,
        legend=legend,
        include_in_legend=include_in_legend,
        xhoverformat=date_format,
    )

    if reverse_plot_order:
        traces_iterable = reversed(list(traces_iterable))

    out_traces = []
    num_existing_traces = sum(1 for _ in figure.select_traces())
    for tid, trace, in enumerate(traces_iterable, start=num_existing_traces, ):
        custom_data = (tid, )
        trace.update(customdata=custom_data, )
        figure.add_trace(trace, **row_column, )
        out_traces.extend(figure.select_traces({"customdata": custom_data}, ))

    # REFACTOR
    xaxis = _cp.deepcopy(_PLOTLY_STYLES["layouts"]["plain"]["xaxis"])
    yaxis = _cp.deepcopy(_PLOTLY_STYLES["layouts"]["plain"]["yaxis"])
    layout = _cp.deepcopy(_PLOTLY_STYLES["layouts"]["plain"])
    del layout["xaxis"]
    del layout["yaxis"]

    layout["showlegend"] = show_legend

    if xaxis_type is None:
        xaxis_type = periods[0].plotly_xaxis_type if periods else "linear"
    xaxis["type"] = xaxis_type
    xaxis["tickformat"] = date_format
    xaxis["ticklabelmode"] = date_axis_mode

    figure.update_xaxes(xaxis, **row_column, )
    figure.update_yaxes(yaxis, **row_column, )
    figure.update_layout(layout or {}, )

    if legend_order is not None:
        figure.update_layout({"legend_traceorder": legend_order, }, )

    if bar_mode is not None:
        figure.update_layout({"barmode": bar_mode, }, )

    if bar_norm is not None:
        figure.update_layout({"barnorm": bar_norm, }, )

    if freeze_span:
        _ez_plotly.freeze_span(figure, periods, subplot, )

    if figure_title is not None:
        figure.update_layout({"title.text": figure_title, }, )

    if update_layout is not None:
        figure.update_layout(update_layout, )

    if subplot_title:
        _ez_plotly.update_subplot_title(figure, subplot_index, subplot_title, )

    if xline is not None and vline is None:
        vline = xline

    if vline is not None:
        _ez_plotly.add_vline(figure, vline, )

    if highlight is not None:
        _ez_plotly.add_highlight(figure, highlight, )

    if show_figure:
        figure.show(renderer=renderer, )

    info = {
        "figure": figure,
        "traces": out_traces,
    } if return_info else None

    return info, figure,

    #]


def _generate_plain_traces(
    series: Series,
    trace_constructor: Callable,
    update_traces: Iterable[dict] | dict | None,
    #
    style_cycle: Iterable[tuple[tuple, ...]],
    from_until: tuple[Period, Period],
    trace_periods: tuple[str, ...],
    transform: Callable,
    legend: Iterable[str] | None,
    include_in_legend: Iterable[bool],
    xhoverformat: str | None = None,
) -> Any:
    """
    """
    #[
    trace_update_cycle = _create_trace_update_cycle(update_traces, )
    #
    if isinstance(include_in_legend, bool):
        include_in_legend = _it.repeat(include_in_legend, )
    #
    legend_cycle = legend or _it.repeat(None, )
    #
    zipped = zip(
        series.iter_own_data_variants_from_until(from_until=from_until, ),
        legend_cycle,
        style_cycle,
        trace_update_cycle,
        include_in_legend,
    )
    for data, name, style, update, include in zipped:
        trace = trace_constructor(
            style=style,
            x=trace_periods,
            y=tuple(transform(i) for i in data),
            name=name,
            showlegend=include and name is not None,
            xhoverformat=xhoverformat,
        )
        trace.update(update, )
        yield trace
    #]


def _generate_band_traces(
    series: Series,
    base_color: str | tuple | None,
    shading_weights: Iterable[float] | None,
    shading_background: str | tuple | None,
    update_band_traces: Iterable[dict] | dict | None,
    update_midline_trace: dict | None,
    #
    style_cycle: Iterable[tuple[tuple, ...]],
    from_until: tuple[Period, Period],
    trace_periods: tuple[str, ...],
    transform: Callable,
    legend: Iterable[str] | None,
    include_in_legend: Iterable[bool],
    xhoverformat: str | None = None,
) -> Any:
    r"""
    """
    #[
    band_trace_update_cycle = _create_trace_update_cycle(update_band_traces, )
    style = next(style_cycle, )
    base_color_string = base_color or style[0]
    base_color_rgba = _ez_plotly.rgba_from_string(base_color_string, )
    base_color_rgba = base_color_rgba[:3] + (1.0, )
    #
    all_data = series.get_data_from_until(from_until=from_until, )
    num_bands = series.num_variants // 2
    has_midline = series.num_variants % 2 == 1
    num_plots = num_bands + int(has_midline)
    all_left_data = all_data[:, :num_bands]
    all_right_data = all_data[:, ::-1][:, :num_bands]
    midline_data = None
    if has_midline:
        midline_data = all_data[:, num_bands]
    #
    if isinstance(include_in_legend, bool):
        include_in_legend = (include_in_legend, ) * num_plots
    else:
        include_in_legend = tuple(include_in_legend)
    #
    legend = legend or _it.repeat(None, )
    legend_cycle = tuple(name for _, name in zip(range(num_plots), legend, ))
    #
    background_rgba = _ez_plotly.rgba_from_string(shading_background, ) if shading_background else None
    shades = _ez_plotly.generate_opaque_shades(
        base_color_rgba,
        num_bands,
        weights=shading_weights,
        background_rgba=background_rgba,
    )
    #
    trace_periods_rev = tuple(reversed(trace_periods, ))
    trace_periods_band = trace_periods + trace_periods_rev
    #
    zipped = zip(
        all_left_data.T,
        all_right_data.T,
        shades,
        legend_cycle,
        band_trace_update_cycle,
        include_in_legend,
    )
    for left_data, right_data, shade, name, update, include in zipped:
        left_data_transformed = tuple(transform(i) for i in left_data)
        right_data_transformed = tuple(transform(i) for i in right_data)
        data_band = left_data_transformed + tuple(reversed(right_data_transformed, ))
        shade_string = _ez_plotly.string_from_rgba(shade, )
        trace = _pg.Scatter(
            x=trace_periods_band,
            y=data_band,
            mode="lines",
            line_color=shade_string,
            fill="toself",
            fillcolor=shade_string,
            name=name,
            showlegend=include and name is not None,
            xhoverformat=xhoverformat,
        )
        trace.update(update, )
        yield trace
    #
    if midline_data is not None:
        midline_data_transformed = tuple(transform(i) for i in midline_data)
        base_color_string = _ez_plotly.string_from_rgba(base_color_rgba, )
        midline_name = legend_cycle[num_bands]
        midline_include = include_in_legend[num_bands] and midline_name is not None
        trace = _pg.Scatter(
            x=trace_periods,
            y=midline_data_transformed,
            mode="lines+markers",
            line_color=base_color_string,
            name=midline_name,
            showlegend=midline_include,
            xhoverformat=xhoverformat,
        )
        trace.update(update_midline_trace)
        yield trace
    #]


def _generate_histogram_traces(
    series: Series,
    hist_norm: str,
    update_traces: Iterable[dict] | dict | None,
    #
    style_cycle: Iterable[tuple[tuple, ...]],
    from_until: tuple[Period, Period],
    trace_periods: tuple[str, ...],  # not used; accepted for interface compatibility
    transform: Callable,
    legend: Iterable[str],
    include_in_legend: Iterable[bool],
    xhoverformat: str | None = None,  # not used; accepted for interface compatibility
) -> Any:
    r"""
    """
    #[
    trace_update_cycle = _create_trace_update_cycle(update_traces, )
    #
    if isinstance(include_in_legend, bool):
        include_in_legend = _it.repeat(include_in_legend, )
    #
    legend_cycle = legend or _it.repeat(None, )
    #
    zipped = zip(
        series.iter_own_data_variants_from_until(from_until=from_until, ),
        legend_cycle,
        style_cycle,
        trace_update_cycle,
        include_in_legend,
    )
    for data, name, style, update, include in zipped:
        trace = _pg.Histogram(
            x=tuple(transform(i) for i in data),
            histnorm=hist_norm,
            marker_color=style[0],
            name=name,
            showlegend=include and name is not None,
        )
        trace.update(update, )
        yield trace
    #]


def _create_transform_function(
    round_to: int | None = None,
) -> Callable[[Real], Real]:
    """
    """
    #[
    def no_transform(x: Real, ) -> Real:
        return x

    def decorate_round(func: Callable, ) -> Callable:
        def wrapper(x: Real, ) -> Real:
            return round(func(x), round_to, )
        return wrapper

    transform = no_transform

    if round_to is not None:
        transform = decorate_round(transform, )

    return transform
    #]


def _create_trace_update_cycle(
    update_traces: Iterable[dict] | dict | None = None,
) -> Iterable[dict]:
    r"""
    """
    #[
    if update_traces is None:
        return _it.repeat({}, )
    elif isinstance(update_traces, dict):
        return _it.repeat(update_traces, )
    return _it.cycle(update_traces, )
    #]

