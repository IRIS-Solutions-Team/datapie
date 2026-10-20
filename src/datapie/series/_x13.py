r"""
Interface to X13-ARIMA-TRAMO-SEATS
"""


#[

from __future__ import annotations

# Typing imports
from typing import Literal, TYPE_CHECKING

# Standard library imports
import os as _os
import numpy as _np
import subprocess as _sp
import tempfile as _tf
import copy as _co
import glob as _gl

# Third-party imports
import documark as _dm

# Application imports
from .. import wrongdoings as _wrongdoings
from .. import has_variants as _has_variants
from ..periods import Period, Span
from ..frequencies import Frequency

from .. import x13_runners_1_1_39
from .. import x13_runners_1_1_62

# Local imports
from ._functionalize import FUNC_STRING

# Type checking imports
if TYPE_CHECKING:
    from typing import Any
    from types import EllipsisType
    from ..series import Series

#]


ModeType = Literal[
    "mult",
    "add",
    "pseudoadd",
    "logadd",
]


OutputType = Literal[
    "seasonal",
    "seasonally_adjusted",
    "trend_cycle",
    "irregular",
    "seasonal_and_td",
    "holiday_and_td",
]


_X13_RUNNER_VERSION_DISPATCH = {
    "1.1.39": x13_runners_1_1_39.run_x13_executable,
    "1.1.62": x13_runners_1_1_62.run_x13_executable,
}


class Mixin:
    #[

    @_dm.reference(category="filtering", )
    def x13(
        self,
        *,
        span: Span | EllipsisType = ...,
        when_error: _wrongdoings.HOW = "warning",
        clean_up: bool = True,
        output: OutputType = "seasonally_adjusted",
        #
        return_info: bool = False,
        unpack_singleton: bool = True,
        #
        specs_template: dict[str, Any] | None = None,
        mode: Literal["mult", "add", "pseudoadd", "logadd", ] | None = None,
        allow_missing: bool = False,
        add_to_specs: dict[str, Any] | None = None,
        #
        version: Literal["1.1.39", "1.1.62", ] = "1.1.62",
    ) -> dict[str, Any]:
        r"""
==Replace a series with an X13 seasonal-adjustment component==

#### Syntax

##### Method form

    x.x13(
        span=...,
        when_error="warning",
        clean_up=True,
        output="seasonally_adjusted",
        return_info=False,
        unpack_singleton=True,
        specs_template=None,
        mode=None,
        allow_missing=False,
        add_to_specs=None,
        version="1.1.62",
    )

    info = x.x13(
        return_info=True,
    )

##### Function form

    new_series = datapie.x13(
        x,
        span=...,
        when_error="warning",
        clean_up=True,
        output="seasonally_adjusted",
        return_info=False,
        unpack_singleton=True,
        specs_template=None,
        mode=None,
        allow_missing=False,
        add_to_specs=None,
        version="1.1.62",
    )

    new_series, info = datapie.x13(
        x,
        return_info=True,
    )

#### Input arguments

!!! input "span"
    The periods to process; the default, `...`, means the current span. Must be nonempty. Observations outside the first and last requested periods are removed.

!!! input "when_error"
    What to do if X13 does not produce a result: `"warning"` (the default) warns, `"error"` raises an error, and `"silent"` continues without a warning. This does not handle errors before or during program execution.

!!! input "clean_up"
    Whether to remove temporary specification and output files after the run. The default is `True`. With `False`, the files remain in the current working directory.

!!! input "output"
    The component to keep. The default is `"seasonally_adjusted"` (`"sa"`). Other choices are `"seasonal"` (`"sf"` or `"seasonal_factors"`), `"trend_cycle"` (`"tc"`), `"irregular"` (`"irr"`), `"seasonal_and_td"`, and `"holiday_and_td"`. An X13 table name may also be supplied.

!!! input "return_info"
    Whether to return details of the run. The default is `False`.

!!! input "unpack_singleton"
    With `return_info=True`, whether to return a single information dictionary for a one-variant series rather than a one-element list. The default is `True`.

!!! input "specs_template"
    An optional dictionary replacing the default X13 specification. The default, `None`, uses the built-in `series`, `transform` and `x11` settings.

!!! input "mode"
    The decomposition mode: `"mult"`, `"add"`, `"pseudoadd"` or `"logadd"`. The default, `None`, selects multiplicative mode when all nonmissing values have the same strict sign, and additive mode otherwise.

!!! input "allow_missing"
    Whether to add automatic ARIMA modeling when no ARIMA model is specified. The default is `False`. This setting supports missing observations in the X13 run.

!!! input "add_to_specs"
    An optional dictionary of settings to add to, or update in, the chosen specification. The default is `None`.

!!! input "version"
    The bundled X13 version: `"1.1.39"` or `"1.1.62"`. The default is `"1.1.62"`.

#### Method form returns

!!! returns "None"
    With `return_info=False`, the series is changed in place and nothing is returned.

!!! returns "info"
    With `return_info=True`, the series is changed in place and information about the run is returned: a dictionary for a single variant or a list of dictionaries for several variants. With `unpack_singleton=False`, the result is always a list.

#### Function form returns

!!! returns "new_series"
    With `return_info=False`, return the adjusted copy. The input series is unchanged.

!!! returns "new_series, info"
    With `return_info=True`, return `(new_series, info)`, using the same information format as the method form. The input series is unchanged.

All options are keyword-only. Only monthly and quarterly data are supported. The method clips the input before running X13; a later error does not restore removed observations. If X13 fails and the error policy allows continuation, its result is missing and may leave the series empty.

??? note "Details"
    The information dictionaries include whether the run succeeded, the selected mode and transformation, the specification, and collected X13 output.

    Variants are processed separately, but the automatic mode is chosen from the series as a whole. Entirely negative data are reversed in sign for processing and reversed back afterwards. Missing observations prevent this reversal, even if the selected mode is multiplicative.

    Each variant needs at least one available observation. Trailing missing values are not currently handled successfully by the endpoint-removal routine.
        """
        span = self.resolve_periods(span)
        base_start, base_end = span[0], span[-1]
        self.clip(base_start, base_end, )
        #
        mode, transform_function, flip_sign = _resolve_mode(self, mode, )
        basic_settings = _prepare_basic_settings(
            base_start, output,
            mode=mode,
            transform_function=transform_function,
        )
        specs_template = _get_specs_template(specs_template, )
        _update_specs_template_with_extra_settings(specs_template, add_to_specs, allow_missing, )
        specs_template_string = _print_specs_template(specs_template, )
        specs_template_string = _insert_basic_settings_into_specs_template_string(specs_template_string, basic_settings, )
        run_x13_executable = _X13_RUNNER_VERSION_DISPATCH[version]
        #
        new_data = []
        out_info = []
        for variant_data in self.data.T:
            info_v = {
                "specs_template": specs_template,
                "mode": mode,
                "transform_function": transform_function,
                "flip_sign": flip_sign,
            }
            if flip_sign:
                variant_data = -variant_data
            new_data_v = _x13_data(
                specs_template_string,
                base_start,
                variant_data,
                basic_settings["x11_save"],
                run_x13_executable,
                info=info_v,
                clean_up=clean_up,
                version=version,
            )
            if flip_sign:
                new_data_v = -new_data_v
            new_data.append(new_data_v.reshape(-1, 1, ), )
            out_info.append(info_v, )
            #
        if not all(i["success"] for i in out_info):
            message = "X13 failed to produce a result for at least one variant."
            _wrongdoings.raise_as(when_error, message, )
        #
        new_data = _np.hstack(new_data, )
        self._replace_start_and_values(base_start, new_data, )
        #
        if return_info:
            out_info = _has_variants.unpack_singleton(
                out_info, self.is_singleton,
                unpack_singleton=unpack_singleton,
            )
            return out_info
        else:
            return

    #]


_functional_forms = {"x13", }


for n in _functional_forms:
    exec(FUNC_STRING.format(n=n, ), globals(), locals(), )


__all__ = tuple(_functional_forms)


def _x13_data(
    specs: str,
    base_start: Period,
    base_variant_data: _np.ndarray,
    x11_save: str,
    run_x13_executable: Callable,
    *,
    info: dict[str, Any],
    clean_up: bool = True,
    version: Literal["1.1.39", "1.1.62", ] = "1.1.62",
) -> tuple[_np.ndarray, dict[str, Any]]:
    """
    """
    #[
    new_data = _np.full(base_variant_data.shape, _np.nan, dtype=float, )
    start_date, variant_data, output_slice = _remove_leading_trailing_nans(base_start, base_variant_data, )
    year, segment = start_date.to_year_segment()
    specs = specs.replace("$(series_start)", _X13_DATE_FORMAT_RESOLUTION[start_date.frequency].format(year=year, segment=segment, ), )
    specs = specs.replace("$(series_data)", _print_series_data(variant_data, ), )
    specs_file_name_without_ext = _write_specs_to_file(specs, )
    system_output = run_x13_executable(specs_file_name_without_ext, )
    raw_output_data, update_info = _collect_outputs(specs_file_name_without_ext, system_output, x11_save, )
    info.update({"specs": specs, })
    info.update(update_info, )
    if raw_output_data is not None:
        new_data[output_slice] = raw_output_data
    if clean_up:
        _clean_up(specs_file_name_without_ext, )
    return new_data
    #]


def _print_series_data(
    variant_data: _np.ndarray,
) -> str:
    """
    """
    _INDENT = " " * 8
    _NAN_REPLACEMENT = "-99999.0"
    data_str = "\n".join(
        _INDENT + (f"{v:g}" if not _np.isnan(v) else _NAN_REPLACEMENT)
        for v in variant_data
    )
    return data_str


# def _execute(
#     specs_file_name_without_ext: str,
# ) -> _sp.CompletedProcess:
#     """
#     """
#     #[
#     return _sp.run(
#         [_X13_EXECUTABLE_PATH, specs_file_name_without_ext, ],
#         stdout=_sp.PIPE,
#         check=True,
#     )
#     #]


def _collect_outputs(
    specs_file_name_without_ext: str,
    output: _sp.CompletedProcess,
    out_table: str,
) -> tuple[_np.ndarray | None, dict[str, str]]:
    """
    """
    #[
    info = _read_out_files(specs_file_name_without_ext, )
    try:
        info[out_table] = str(info[out_table])
        out_data = _read_output_data(info[out_table], )
    except:
        out_data = None
        info[out_table] = None
    info["success"] = (
        output.returncode == 0
        and "ERROR" not in str(output.stdout)
        and out_data is not None
    )
    return out_data, info
    #]


def _read_output_data(
    out_table: str,
) -> tuple[tuple[float, ...], str]:
    """
    """
    return tuple(float(i) for i in out_table.split()[5::2])


def _read_out_files(
    specs_file_name_without_ext: str,
) ->  dict[str, str]:
    """
    """
    #[
    info = dict()
    for file_name in _gl.glob(specs_file_name_without_ext + ".*"):
        ext = file_name.split(".")[-1]
        encoding = None if ext != "err" else "latin-1"
        with open(file_name, "rt", encoding=encoding, ) as fid:
            info[ext] = fid.read()
    return info
    #]


def _write_specs_to_file(
    specs: str,
) -> str:
    """
    """
    with _tf.NamedTemporaryFile(dir=".", mode="wt", suffix=".spc", delete=False, ) as fid:
        specs_file_name = fid.name
        fid.write(specs)
    return specs_file_name.removesuffix(".spc")


def _remove_leading_trailing_nans(
    base_start: Period,
    variant_data: _np.ndarray,
) -> tuple[Period, _np.ndarray, slice]:
    """
    """
    #[
    start_date = base_start.copy()
    num_rows = variant_data.shape[0]
    num_leading = 0
    num_trailing = 0
    while _np.isnan(variant_data[0]):
        num_leading += 1
        variant_data = variant_data[1:]
    while _np.isnan(variant_data[-1]):
        num_trailling += 1
        variant_data = variant_data[:-1]
    return start_date + num_leading, variant_data, slice(num_leading, num_rows-num_trailing, )
    #]


_TRANFORM_FUNCTION_DISPATCH = {
    "mult": "log",
}


def _resolve_mode(
    self: Series,
    mode: ModeType | None,
    transform_function: str | None = None,
) -> tuple[str, str, bool]:
    r"""
    """
    #[
    flip_sign = False
    if mode is None:
        all_positive = _np.all((self.data > 0) | _np.isnan(self.data))
        all_negative = _np.all((self.data < 0) | _np.isnan(self.data))
        is_sign_strict = all_positive or all_negative
        mode = "mult" if is_sign_strict else "add"
    if transform_function is None:
        transform_function = _TRANFORM_FUNCTION_DISPATCH.get(mode, "none", )
    flip_sign = _np.all(self.data < 0)
    return mode, transform_function, flip_sign,
    #]


def _prepare_basic_settings(
    base_start: Period,
    output: str,
    mode: ModeType,
    transform_function: str = "none",
) ->  dict[str, str]:
    """
    """
    #[
    return {
        "series_period": str(base_start.frequency.value),
        "x11_mode": str(mode),
        "x11_save": _X11_OUTPUT_RESOLUTION.get(output, output),
        "transform_function": str(transform_function),
    }
    #]


def _get_specs_template(
    specs_template: dict[str, Any] | None,
) -> dict[str, Any]:
    """Get specs template either from a custom dict or a default dict"""
    return _co.deepcopy(specs_template or _DEFAULT_TEMPLATE)


def _update_specs_template_with_extra_settings(
    specs_template: dict[str, Any] | None,
    add_to_specs: dict[str, Any] | None,
    allow_missing: bool,
) -> None:
    """Update specs template with extra custom settings"""
    #[
    if add_to_specs:
        for k, v in add_to_specs.items():
            if k in specs_template:
                specs_template[k].update(v, )
            else:
                specs_template[k] = v
    _add_arima_model_if_needed(specs_template, allow_missing, )
    #]


def _add_arima_model_if_needed(
    specs_template: dict[str, Any],
    allow_missing: bool,
) -> None:
    """Add arima model if not present and in-sample missing values are allowed"""
    #[
    if not allow_missing:
        return
    has_arima = (
        ("automdl" in specs_template and specs_template["automdl"] is not False)
        or ("arima" in specs_template and specs_template["arima"] is not False)
    )
    if not has_arima:
        specs_template["automdl"] = {}
    #]


def _print_specs_template(
    specs_template: dict[str, Any],
) -> str:
    """Print the specs template dict to a string"""
    #[
    specs_template_string = "\n"
    for k, v in specs_template.items():
        if v is False:
            continue
        add = "\n\n" + k.lower() + "{"
        if isinstance(v, dict) and v:
            for kk, vv in v.items():
                add += f"\n    {kk.lower()}={vv}"
        add += "\n}"
        specs_template_string += add
    specs_template_string += "\n"
    return specs_template_string
    #]


def _insert_basic_settings_into_specs_template_string(
    specs_template_string: str,
    settings: dict[str, str],
) -> str:
    """
    Replace placeholders with custom setting
    """
    #[
    for k, v in settings.items():
        specs_template_string = specs_template_string.replace(f"$({k})", v)
    return specs_template_string
    #]


def _clean_up(
    specs_file_name_without_ext: str,
) -> None:
    """
    """
    #[
    for f in _gl.glob(specs_file_name_without_ext + ".*"):
        _os.remove(f, )
    #]


_DEFAULT_SERIES_TEMPLATE = {
    "start": "$(series_start)",
    "data": "(\n$(series_data)\n    )",
    "period": "$(series_period)",
    "decimals": 5,
    "precision": 5,
}

_DEFAULT_TRANSFORM_TEMPLATE = {
    "function": "$(transform_function)",
}

_DEFAULT_X11_TEMPLATE = {
    "mode": "$(x11_mode)",
    "save": "$(x11_save)",
}

_DEFAULT_TEMPLATE = {
    "series": _DEFAULT_SERIES_TEMPLATE,
    "transform": _DEFAULT_TRANSFORM_TEMPLATE,
    "x11": _DEFAULT_X11_TEMPLATE,
}

_X11_OUTPUT_RESOLUTION = {
    "sf": "d10",
    "seasonal": "d10",
    "seasonal_factors": "d10",
    "sa": "d11",
    "seasonally_adjusted": "d11",
    "tc": "d12",
    "trend_cycle": "d12",
    "irr": "d13",
    "irregular": "d13",
    "seasonal_and_td": "d16",
    "holiday_and_td": "d18",
}

_X13_DATE_FORMAT_RESOLUTION = {
    Frequency.MONTHLY: "{year:04d}.{segment:02d}",
    Frequency.QUARTERLY: "{year:04d}.{segment:1d}",
}

