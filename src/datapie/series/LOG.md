# Bug / Documentation Log — `datapie/src/datapie/series`

This log was compiled with AI assistance during the documentation rewrite. As I am
new to the codebase, I have not attempted to judge which findings are intentional
design and which are defects — everything observed is recorded here, and I would
welcome a review from someone who knows the module. Line numbers refer to the
source as of 2026-07-31 and were re-checked against it. Items marked *(observed)*
were confirmed by running the package earlier; they were not re-run for this pass,
and everything else was re-verified by reading the code.

**Scope:** one block per file in the `series` folder. Every block has the same
three sections, in the same order:

| Section | Contents |
| ------- | -------- |
| **Bugs** | The code does the wrong thing, or crashes. |
| **Docs vs code** | The docstring and the code disagree; typos. |
| **Notes** | Verified behaviour, dead code, style, open questions. |

---

## Already fixed — not part of the log

`_timing.py` — `redate` was broken for every call. The body tested `old_data`
while the parameter is `old_date`, so the function raised `NameError` before
reaching either branch. The typo was corrected; this is the only code change made
anywhere. The function now works in both modes — with `old_date` omitted the start
becomes `new_date`, and with it supplied the series slides so the observation at
`old_date` lands on `new_date`.

---

## `_apply_to_variants.py`

*(These surface through the four filters in `_uv_filters.py`, but the code is
here.)*

### Bugs

1. **`_apply_to_variants` mutates before it validates.** `self.data = extended_data`
   and `self.start = extended_periods[0]` run at lines 87-88, before `func` is
   called at line 100. If `func` returns the wrong type or shape, the
   `TypeError`/`ValueError` fires at lines 103-113 — after the series has already
   been extended with missing periods and its start moved. A caught exception
   leaves a silently altered series.
2. **NaN padding uses the series dtype.** Lines 160 and 165 build the pad with
   `_np.full(..., _np.nan, dtype=self.data.dtype)`. For an integer-typed series
   that will not produce missing values.

### Docs vs code

None.

### Notes

1. The `periods` argument is dead in all four kernels. `_apply_to_variants` builds
   `periods_tuple` (line 81) and passes it, and not one of `_cum_avg`,
   `_exp_smooth`, `_double_exp_smooth`, `_decay_avg` reads it.

---

## `_broadcasts.py`

### Bugs

1. **`broadcast_variants_when_needed` mutates its second argument, and the two
   call sites differ.** `_lays.py:92` (`overlay_by_span`) passes a copy;
   `_lays.py:192` (`overlay_by_observation`) passes `other` directly. *(observed)*
   `x.overlay_by_observation(y)` raised `y.num_variants` from 1 to 3, while
   `a.overlay_by_span(b)` left `b.num_variants` at 1. Same finding as `_lays.py`
   bug 1.

### Docs vs code

None.

### Notes

1. `broadcast_variants(0)` is accepted and empties the series.
   `_np.repeat(data, 0, axis=1)` produces shape `(n, 0)` and `is_empty` becomes
   `True`. No caller passes zero, so this is a latent robustness gap, not critical.
   Negative counts were not tested.

---

## `_conversions.py`

### Bugs

1. **`select` never works.** `_aggregate_within_data` converts it to a tuple
   (line 539), which numpy reads as one index per dimension. Two or more entries
   raise `IndexError`; one entry indexes to a scalar and fails in the aggregation
   function with `TypeError`. No input succeeded. *(observed)*
2. **`_wrongdoings` is used at line 341 but never imported.** Disaggregating in the
   wrong direction raises `NameError` instead of `Critical`.
3. **An unknown `method` raises `KeyError` at line 332**, before the frequency
   checks at lines 334-343, so a wrong frequency direction is masked.
4. **`disaggregate` is annotated `-> Self`** (line 224) but returns `None` on both
   paths (line 335, and the fall-through at line 347).
5. **`aggregate` has no `else`** after the `is_regular` / `DAILY` branch
   (lines 151-154), leaving `aggregate_func` possibly unbound. Not reachable today
   — the only frequency that would get there, `WEEKLY`, has no period class and
   raises `KeyError` at line 142 first.
6. **`Literal` (line 51, in `aggregate`) and `Real` (lines 569, 579, 589, in the
   `convert_*` functions) are used but never imported.** Harmless at runtime
   because of `from __future__ import annotations`; `typing.get_type_hints` would
   fail.
7. **`convert_diff` is missing from `_functional_forms`** (lines 394-397), so
   unlike `convert_roc` and `convert_pct` it is not exported.

### Docs vs code

1. `aggregate` and `disaggregate` have their `target_freq` descriptions swapped:
   line 90 says the series "will be diaggregated" and line 255 says "will be
   aggregated". "diaggregated" is also a typo.
2. `disaggregate` describes `method` as an aggregation function applied within each
   low-frequency period (lines 257-259) — text copied from `aggregate`, wrong here.
3. `aggregate` documents returns `self` and `new` (lines 117-121); the method
   returns `None`.
4. The `aggregate` method table (lines 96-104) omits `"geometric_mean"`, which
   works (line 549). The `Literal` annotation on line 51 omits both `"prod"` and
   `"geometric_mean"`.
5. `disaggregate` shows `model=None` in its usage block (line 247); `model` is not
   in the signature and reaches `disaggregate_arip` through `**kwargs` as a
   required positional argument.

### Notes

None.

---

## `_extrapolate.py`

### Bugs

1. **`Self` is used in the signature on line 36 but never imported**, not even
   under `TYPE_CHECKING`. Harmless only because
   `from __future__ import annotations` leaves annotations unevaluated.
2. **`_extrapolate_data` is annotated `-> None`** (line 229) but returns an array
   (line 242).
3. **`log=True` with a non-positive starting value** produces
   `RuntimeWarning: invalid value encountered in log` and a missing result.
   *(observed)*

### Docs vs code

1. The Returns section documents `self` and `new` (lines 99-103); the method
   returns `None`.
2. The functional-form block shows `extrapolate(self, ...)` (line 52) with no
   package prefix, unlike the sibling files which write `irispie.`.
3. Typos, left in place: "autorergressive" (line 89), "initial condion"
   (line 118), "coefficents" (line 121), and `ar_coeff` for `ar_coeffs`
   (line 122).

### Notes

1. `ar_coeffs` accepts a bare number for a first-order process:
   `x.extrapolate(0.5, span)` behaves as `[0.5]` (line 134). *(observed)*
2. Coefficient order confirmed: `[0.5, 0.25]` on `[1,2,3,4]` gives 2.75, i.e.
   0.5·4 + 0.25·3. *(observed)*
3. `intercept=10` on `[1,2,3,4]` with `[0.5]` gives 12.0, 16.0. *(observed)*
4. `log=True` with `ar_coeffs=[1.0]` and `intercept=log(2)` doubles each period:
   16.0, 32.0. *(observed)*
5. Multiple variants are handled correctly, unlike `lonf` in `_ell_one.py`, which
   drops all but the first.
6. The functional form works: `dp.extrapolate(x, [0.5], span)` returns a new series
   and leaves `x` unchanged, and `'extrapolate' in dp.__all__` is `True`. This
   file's exec loop does pass `globals()` (line 214). *(observed)*

---

## `_filling.py`

### Bugs

None.

### Docs vs code

1. The docstring documents `*args` and shows
   `fill_missing(self, method, *args, span=None)` (lines 67-81, 103-110). The
   signature is `(method, method_args=None, span=None)` — a single extra argument,
   not varargs. Passing two extras fails:
   `TypeError: Mixin.fill_missing() takes from 2 to 4 positional arguments but 5 were given`.
   *(observed)*
2. The docstring calls `"linear"` and `"log_linear"` "interpolation or
   extrapolation" (lines 99-100). They do not extrapolate: past the last
   observation `_fill_interp` repeats the end value (lines 252-257).
3. Returns documents `self` and `new` (lines 119-123); the method returns `None`.
4. The method table omits the `"series"` alias for `"from_series"` (line 384).

### Notes

None.

---

## `_hp.py`

### Bugs

1. **`hpf(x, span=[])` raises `wrongdoings.Error: Invalid Series object constructor`.**
   `_data_hpf` returns `new_start_date=None` alongside empty arrays
   (lines 587-590), and the constructor rejects that combination
   (the `_SERIES_POPULATOR` table in `main.py` has no populator for that case). *(observed)*

### Docs vs code

1. The default `smooth` for monthly data is wrong by a factor of ten. The docstring
   table (line 268) says 144,000; `_AUTO_SMOOTH` computes `(10*12)**2 = 14400`
   (line 36). The other frequencies and the fallback are correct. 14400 is the
   documented value in the new block.
2. The gap formula holds only for `log=False`. The algorithm section (line 372)
   defines the gap as ŷ ≡ y − ȳ. With `log=True` both components are exponentiated
   at the end (lines 592-594), so the returned gap is y / ȳ. *(observed)*
   `np.allclose(gap, data/trend)` is `True`, `np.allclose(gap, data-trend)` is
   `False`.
3. `information` is undocumented. It is a real user-facing argument (`_data_hpf`,
   line 535). `"one_sided"` reruns the two-sided filter once per period
   (lines 109-122); its final-period value matches the two-sided result while
   earlier periods differ.
4. The whole reference docstring hangs on `Series.hpf`, which raises
   `NotImplementedError` (line 377) — so the one entry point a reader would try
   after reading it is the one that does not work. The working routines are the
   module-level `hpf` (line 450) and the `hpf_trend` / `hpf_gap` methods.
5. Typos, left in place: "entier" (line 296), "unline" (line 303).

### Notes

None.

---

## `_jsonables.py`

### Bugs

1. **The multi-variant dead end.** The `ValueError` at line 86 instructs you to set
   `allow_multiple_variants=True`, and that flag's only effect is to raise
   `NotImplementedError` on the first line of the method (lines 82-83). A
   multi-variant series cannot be serialized by any route.
2. **`jsonable["start"]` is read unconditionally at lines 217-219**, before any
   check. A round trip is safe because `to_jsonable` always writes that key, but
   any hand-built or externally-produced dictionary without it raises a bare
   `KeyError: 'start'` rather than anything that says what was expected. Same
   pattern for `jsonable["values"]` (line 221).

### Docs vs code

1. The two sides use different names for the same switch: `include_frequency` /
   `include_description` when writing (lines 35-36), `frequency_included` /
   `description_included` when reading (lines 158-159). Nothing checks that they
   agree.

### Notes

1. The `#]` fold marker on the last line (line 288) sits at 8 spaces, inside
   `from_jsonable`, while the class opened its `#[` at 4 (line 27). The class has no
   closing marker at its own level.
2. `Databox` has the same typo twice in a `call_name`: `databoxes/_jsonables.py:121`
   (`Databox.seres_from_jsonable`) and `databoxes/_jsonables.py:174`
   (`Databox.seres_from_json_file`). Noted since these are the reference names for
   the matching readers.

---

## `_lays.py`

### Bugs

1. **`overlay_by_observation` modifies its argument.** It is the only one of the
   four that does not copy `other` before calling
   `broadcast_variants_when_needed` (line 192, against lines 91-92, 299, 385).
   *(observed)* with a 3-variant `self` and a 1-variant `other`:

   | Method | `other` variants |
   | --- | --- |
   | `overlay_by_span` | 1 → 1 |
   | `overlay_by_observation` | 1 → 3 |
   | `underlay_by_span` | 1 → 1 |
   | `underlay_by_observation` | 1 → 1 |

### Docs vs code

1. Both `by_span` docstrings document an input called `method`, described as
   currently only accepting `"by_span"` (lines 62-64 and 271-273). Neither signature
   has such a parameter; both are `(self, other)`.
2. Grammar slip repeated in both `by_span` docstrings: "The observations from the
   `self` time series used to fill" (lines 81-82) and "from the `other` time series
   used to fill" (lines 289-290) — missing "are".

### Notes

None.

---

## `_moving.py`

### Bugs

1. **A positive window produces a misleading error.** `window_length = -window`
   (line 127) makes the pad width negative at line 130, so
   `ValueError: index can't contain negative values` comes back — telling the user
   the opposite of their mistake. *(observed)* `window=4` and `window=0` both fail
   this way; `window=-4` works.
2. **`moving_window` passes `axis=2` to `func`** (line 139), so a one-argument
   function raises `TypeError: got an unexpected keyword argument 'axis'`.

### Docs vs code

1. The default-window table (lines 97-103) omits half-yearly. Defaults come from the
   enum, not the table: `_get_default_moving_window` returns `-frequency.value` when
   that value is positive (line 380). *(observed)* on real series — yearly -1,
   half-yearly -2, quarterly -4, monthly -12, daily -365, with integer and unknown
   falling back to -4.
2. The overview table (lines 46-51) omits `moving_window` itself, which is exported
   (`'moving_window' in dp.__all__` is `True`, line 358) and callable both as a
   method and as `dp.moving_window(x, np.max, -3)`.
3. `mov_mean`'s docstring heading reads "Moving average" (line 272), duplicating
   `mov_avg`. The two bodies are identical (lines 241 and 280).

### Notes

1. Weekly is unreachable. `PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION`
   (`periods.py:2476-2484`) has no `WEEKLY` entry and there is no `dp.ww`
   constructor, so no weekly series can exist to receive the -52 default. The rule
   produces it correctly; nothing can use it.
2. A missing observation poisons every window touching it:
   `[1, 2, 3, nan, 5, 6, 7, 8]` with `window=-3` gives
   `[6.0, nan, nan, nan, 18.0, 21.0]`. *(observed)*

---

## `_plotly.py`

### Bugs

1. **`plot` dispatches on substrings.** Lines 93 and 95 use
   `elif chart_type in "bar"` and `elif chart_type in "bar_group"` instead of `==`.
   Any string contained in "bar" is silently accepted as a bar chart —
   *(observed)* for `""`, `"b"`, `"a"`, `"r"`, `"ba"` and `"ar"`. Only strings that
   are neither substrings nor valid names reach the `ValueError` at line 108.
2. **`plot_bands` mutates the caller's `update_layout`.** Lines 219-220 call
   `.setdefault("legend_traceorder", "reversed")` on the dictionary the caller
   passed. *(observed)* `{'title_text': 'mine'}` comes back with an extra key.
   Documented in the block, since it is a live side effect rather than a typo.
3. **Dead statement in `plot`, line 91:** `trace_constructor=_line_constructor,` —
   the trailing comma makes it a tuple assigned to a local that is never read.

### Docs vs code

1. The `Literal` annotation for `chart_type` on line 85 omits `"histogram"`, which
   the body handles (line 105) and the error message advertises (line 108).

### Notes

1. None of this file reaches the reference documentation. `__all__ = ()` (line 45),
   no method carries `@_dm.reference`, `documark` is not even imported, and every
   docstring is empty, so nothing appears in `help()` either. This is the package's
   main charting interface. The methods are documented anyway; worth deciding
   whether they should be decorated.
2. The real parameters of every `plot_*` method live in `_create_layout` (line 465
   onwards) and cannot be discovered from the method signatures, which show only
   `**kwargs`.
3. `plot_bands` sets `legend_traceorder` twice by two different routes — once
   through `update_layout` (line 220), once through `legend_order="reversed"`
   (line 225).

---

## `_temporal.py`

### Bugs

1. **`roc_from_aroc` converts in the wrong direction.** It computes
   `self.data**factor` (line 803), while every sibling divides by the factor
   (`roc_from_apct` line 762 and `pct_from_apct` line 721 both use `**(1/factor)`).
   It annualizes a second time instead of undoing the annualization. On a quarterly
   series growing 10% per quarter, `aroc` gives 1.4641 and `roc_from_aroc` returns
   4.594973 rather than recovering 1.1. `roc_from_apct` recovers it correctly from
   the same data. *(observed)*
2. **`cum_diff_log`'s default `initial` of 0 guarantees a zero series.**
   `_CUMULATIVE_FACTORY["diff_log"]` sets `"initial": 0` (line 1220), but its
   forward function is `x_past * exp(change)` (line 1218), so zero is absorbing.
   `cum_diff_log()` returns all zeros; `cum_diff_log(initial=100.)` works. It should
   default to 1, as `pct` and `roc` do. The old docstring states the same wrong
   default as though it were sensible (line 1052). *(observed)*
3. **The annualization factor is -1 for unknown frequency.** Every annualized method
   uses `self.frequency.value or 1` (lines 348, 431, 515, 599, 720, 761, 802), and
   `Frequency.UNKNOWN.value` is -1 (`frequencies.py:87`), which is truthy. `INTEGER`
   (value 0) falls back correctly.
4. **A bad shift string leaks a private attribute name.** `_catch_invalid_shift`
   validates only non-strings (line 1238), so `diff("nonsense")` reaches the
   shifting machinery and raises
   `AttributeError: 'Series' object has no attribute '_shift_nonsense'`. The lookup
   is case- and whitespace-sensitive, so `"YOY"` and `"yoy "` fail the same way with
   no guidance.
5. **`temporal_change_conversion` has a body of `pass`** (line 269). It exists only
   to carry documentation; there is no working counterpart of that name.

### Docs vs code

1. `temporal_change`'s parameter is `by` in the signature (line 39) but is called
   `shift` throughout its docstring (line 141 onwards).
2. The class-method usage block lists `self.difflog(...)` and `self.adifflog(...)`
   (lines 124, 128); the methods are `diff_log` and `adiff_log`.
3. The `shift` description says passing `None` gives -1 (line 143), but
   `shift=None` explicitly raises `TypeError` in `_catch_invalid_shift`
   (`int(None)`, line 1238) — only the signature default supplies -1.
4. `temporal_cumulation`'s Input arguments section (lines 1041-1058) omits
   `func_name` altogether, even though it is the required first parameter
   (line 995). The `initial` entry instead describes the defaults in terms of
   `diff` / `diff_log` / `pct` / `roc`, which are in fact the `func_name` values the
   undocumented parameter takes.
5. Typo: "a give frequency" in the annualization-factor note (line 75).

### Notes

1. Open question: `span.direction` does select between `_cumulate_forward` and
   `_cumulate_backward` (lines 1076-1085), and a reversed span reports
   `direction == "backward"` and runs without error. But the one backward case tried
   returned a single period rather than a rebuilt path. It was not possible to tell
   from the code whether the call was wrong or the backward path is broken, so the
   documentation claims nothing about the result.

---

## `_timing.py`

### Bugs

1. **The sign of a numeric `by` runs opposite to intuition.** `_shift_by_number`
   does `self.start -= by` (defined in `main.py`), so `shift(-1)` moves the series
   later (2020Q1 → 2020Q2) and `shift(1)` moves it earlier. Documented in the block.
2. **An unrecognised string becomes a method name via `getattr`** (lines 59-60), so
   a misspelling surfaces as
   `AttributeError: 'Series' object has no attribute '_shift_nonsense'`. Same leak
   as in `_temporal.py` bug 4.
3. **`ShiftType` in `shift`'s signature (line 26) is never imported here;** it is
   defined at `main.py:65`. `Period` in `redate`'s signature (line 120) is never
   imported here either. Both survive only because
   `from __future__ import annotations` leaves them unevaluated;
   `typing.get_type_hints` on either method would fail.

### Docs vs code

1. Numeric and string forms do fundamentally different things. A number retimes the
   series and leaves the data alone; `"soy"`, `"eopy"` and `"tty"` rewrite the
   values and keep the span (`_shift_soy`, `_shift_eopy` and `_shift_tty` in
   `main.py`). Nothing in the old docstring says
   so.

### Notes

1. `shift("eopy")` empties a series that does not already cover the previous year. A
   2020-only test series came back with `start` `None` and no data, since every
   referenced period lies outside it. *(observed)*

---

## `_uv_filters.py`

*(See also `_apply_to_variants.py`, which the four filters here run through.)*

### Bugs

1. **`_double_exp_smooth` never smooths its second observation.**
   `result[second_valid_idx] = level + slope * periods_between` (line 213) is
   algebraically exactly `values[second_valid_idx]`, since `slope` was just fitted
   to those two points on line 212. Probably intended, but it is invisible from the
   docs.
2. **Mixed gap conventions inside `_double_exp_smooth`.** The initialisation divides
   the slope update by `periods_between` (line 217); the main loop uses a bare
   `slope` with no distance scaling (line 225). Gaps reach the loop through the NaN
   branch (lines 228-234) instead, so the two paths do not treat elapsed time the
   same way.
3. **`__all__` is built from a set.** `_functional_forms` (lines 659-664) is a set
   literal, so `tuple(...)` at line 670 gives an order that is not stable across
   runs. Harmless for imports, not harmless for generated documentation that lists
   exports in order.

### Docs vs code

1. `exp_smooth`'s parameter order is reversed in the docs. The docstring presents
   `alpha` then `span` (lines 323-330); the signature is
   `(self, span=..., alpha=0.3)`. A reader following the docstring writes
   `x.exp_smooth(0.5)` and sets the span.
2. `decay_avg` likewise. The docstring gives `decay` then `span` (lines 502-509);
   the signature is `(self, span=..., decay=0.9)`.
3. `decay_avg` documents the wrong range. The docstring says `(0 < decay < 1)`
   (line 503). The check is `0 < decay <= 1` (line 528). The `ValueError` message on
   the very next line — "exclusive of 0, inclusive of 1" — is correct, so the prose
   contradicts both the code and the error text beside it.
4. `decay_avg` does not mention its own short-circuit. `decay == 1.0` returns
   `_cum_avg(...)` outright (lines 263-264). Only the private `_decay_avg` docstring
   says so; the public one never does.
5. `cum_avg`'s formula is wrong once there is a gap. The docstring gives
   CA_t = (X_1 + ... + X_t) / t (line 604), which holds only for gap-free data. The
   code divides by `count`, the number of observations seen (line 115). Confirmed.
6. No existing docstring mentions gap-filling or span extension, and although all
   four say they modify `self` in place, none says that `start` and `end` move — the
   three behaviours most likely to surprise a caller.
7. `double_exp_smooth`'s docstring gives no hint that its argument order differs
   from its three siblings (`alpha, beta, span` against `span, ...`).

### Notes

1. Stray duplicated `#]` closing `class Mixin` — two in a row, lines 654-655.

---

## `_x13.py`

### Bugs

1. **An all-negative series with a missing observation is sent to X13 unflipped,
   under a log transform. Silent.**

   `_resolve_mode` decides the mode with `_np.all((data < 0) | _np.isnan(data))`
   (line 606), so a missing value does not spoil the strict-sign test and the mode
   comes out `"mult"` with `transform=log`. The flip is decided separately by
   `flip_sign = _np.all(self.data < 0)` (line 611), where `nan < 0` is `False`, so
   the flip does not happen. The two tests treat missing values inconsistently.

   *(observed)* end to end:

   | Case | Mode | `flip_sign` | Success |
   | --- | --- | --- | --- |
   | all negative, clean | mult | `True` | `True` |
   | all negative + NaN | mult | `False` | `False` |

   In the failing case the spec file data begins: `['-100', '-112', '-104']`. The
   binary signals `IEEE_INVALID_FLAG` and returns nothing usable. With the default
   `when_error="warning"` this produces a warning rather than an exception, so a
   script continues with an unadjusted series.
2. **`_remove_leading_trailing_nans` crashes on any variant ending in a missing
   observation.** Line 584 increments `num_trailling` (three l's) while line 586
   returns `num_trailing`. The misspelled name is never initialised, so the call
   raises
   `UnboundLocalError: cannot access local variable 'num_trailling' where it is not associated with a value`.
   *(observed)* by calling the helper directly: leading NaN works, trailing NaN
   raises, clean data works.
3. **`span` clips the input in place before X13 runs.**
   `self.clip(base_start, base_end)` at line 292. A 24-period series given
   `span=Span(qq(2016,1), qq(2019,4))` comes back with 16 periods — observations
   outside the span are removed from the object, not merely excluded from the
   calculation. *(observed)*
4. **Invalid `output` is not validated.** `_X11_OUTPUT_RESOLUTION.get(output, output)`
   (line 628) falls back to passing the string through as an X13 table name.
   `output="nonsense"` produced a "failed to produce a result" warning followed by
   `IndexError: index 0 is out of bounds for axis 0 with size 0`. *(observed)*
5. **Unsupported frequencies fail without explanation.**
   `_X13_DATE_FORMAT_RESOLUTION` (lines 757-760) has entries for monthly and
   quarterly only, so a yearly series raises a bare
   `KeyError: <Frequency.YEARLY: 1>` at line 467.
6. **Temporary files are written to the current working directory.**
   `_write_specs_to_file` uses `_tf.NamedTemporaryFile(dir=".", ...)` (line 563).
   With `clean_up=False`, five `tmp*` files (`.spc`, `.log`, `.out`, `.err`, and the
   requested table) are left wherever the process is running.
7. **`Callable` is used in `_x13_data`'s signature (line 455) but never imported.**
   Survives only because of `from __future__ import annotations`.

### Docs vs code

1. Both usage blocks list `mode` twice among the arguments (lines 106 and 113; lines
   138 and 145).
2. The usage blocks show `new, info = irispie.x13(...)` (line 121) and
   `info = self.x13(...)` (line 153). The method returns only `info`, and only when
   `return_info=True`; otherwise `None` (lines 339-346).
3. The `span` entry (line 169) says "If `span=None` or `span=...`". The signature
   default is `...` and `None` is not handled specially. It says nothing about the
   clipping side effect (bug 3).
4. The `output` table (lines 177-184) omits five working aliases: `"sf"`, `"sa"`,
   `"tc"`, `"irr"` and `"seasonal_factors"` (lines 743-755). All verified working.
   *(observed)*
5. Typos: `_TRANFORM_FUNCTION_DISPATCH` (missing S) at line 590, and "the default
   templated" in the `add_to_specs` entry (line 211).

### Notes

None.

---

## `arip.py`

### Bugs

1. **Circular import between `arip` and `_conversions`.** `arip.py` imports
   `_conversions` at module level (line 16) and `_conversions.py` imports `arip` at
   module level (line 19). This survives only on import ordering, so adding an
   import or importing a submodule directly could break the package.
2. **`_get_first_last_observations` returns a distance, not a count.** It returns
   `where_finite[-1] - where_finite[0]` (line 204), the gap between the first and
   last finite index, under the name `num_low_periods`. Callers use it as a divisor
   when estimating `rho` (line 148) and `const` (line 182), so the growth rate and
   constant are computed over one fewer period than the name implies. With a single
   observation the distance is 0 and the callers fall back to `rho=1` / `const=0`.
3. **`disaggregate_arip` annotation is wrong on both paths.** Annotated `-> Self`
   (line 31), but returns a 2-tuple of `(Period, ndarray)` (line 66), or
   `(None, None)` when there is no start date (line 35).

### Docs vs code

1. The module docstring is empty (lines 1-2).

### Notes

1. The aggregation constraint holds exactly for all ten form/aggregation
   combinations (rate/diff by sum/mean/avg/first/last): each year recovered
   `[100.0, 200.0, 300.0]`. *(observed)*
2. A custom weights tuple must be `num_within` long, so 4 for annual-to-quarterly. A
   12-long tuple raises
   `ValueError: could not broadcast input array from shape (12,) into shape (4,)`.
   *(observed)*
3. A complete target for a low period displaces its observation (line 379). Targets
   `[1, 2, 3, 4]` against an annual 100.0 gave quarters summing to 10.0. A partial
   target with only Q2 pinned to 30 kept the annual constraint, the four quarters
   still summing to 100.0. This is documented in both blocks. *(observed)*
4. Mutation depends on the caller. Through `disaggregate_arip` the input series is
   safe, since `iter_own_data_variants_from_until` yields copies — confirmed by
   writing -999 into a yielded array and finding the series unchanged. That holds
   because `disaggregate_arip` passes an explicit `from_until`; called with `...`
   the same method yields views onto the series' own data and a write does land.
   See `main.py` note 11 — the two findings agree rather than contradict. Calling
   `disaggregate_arip_data` directly modifies the caller's array:
   `[100.0, 200.0, 300.0]` came back as `[nan, 200.0, 300.0]` under a complete
   target. Documented in the block where each applies. *(observed)*
5. Error paths: an unrecognised form raises `KeyError` (line 334), an unrecognised
   aggregation name raises `KeyError` (line 336), and a non-string, non-iterable
   aggregation such as 5, 4.0 or `None` raises `TypeError` (line 337). A `model`
   that is not a 2-tuple, such as the bare string `"rate"`, raises
   `ValueError: too many values to unpack (expected 2)` (line 333). *(observed)*
6. An empty series returns `(None, None)` (line 35). *(observed)*
7. `CHOOSE_AGGREGATION_FUNC` on line 245 is public and referenced nowhere in the
   package. `_CHOOSE_AGGREGATION_VECTOR` (line 236) is the one actually used.
8. Line 30 carries a commented-out `indicator` parameter, now superseded by `target`.
9. `Self`, `Iterable` and `Real` are imported at module level (lines 9-10) rather
   than under `TYPE_CHECKING`, unlike the sibling modules.

---

## `main.py`

*(Findings in this section are anchored on method and function names rather than
line numbers. Documenting this file added over 1600 lines to it, and every number
cited during the pass had to be re-derived twice; names survive the next insertion.
The `has_variants.py` numbers below refer to that file, which was not touched.)*

### Bugs

1. **A plain list in `values` is read as one entry per variant, not per period.**
   `_from_start_and_values` sends a non-array `values` through
   `has_variants.iter_variants`, which for a list returns
   `exhaust_then_last(anything)` (`has_variants.py:223-224`) — an iterator over the
   list's *elements*. It then does
   `column_stack([v for v, _ in zip(values, range(self.num_variants))])`, taking only
   the first element for a single-variant series.
   `Series(start=qq(2020,1), values=[1.0, 2.0, 3.0])` builds a one-period series
   holding 1.0. *(observed)* A tuple or a numpy array behaves as expected. The same
   rule applies through `set_data`, where a list broadcasts its first element across
   every period: `set_data(span, [7., 8., 9.])` writes 7 everywhere. *(observed)*
2. **`get_values()` returns the first variant only.** It calls the module-level
   `_has_variants.unpack_singleton(values, unpack_singleton=...)` without passing
   `self.is_singleton`, and that parameter defaults to `True`
   (`has_variants.py:242-253`), so the list is unpacked whatever the number of
   variants. A two-variant series returns one tuple and the second column is lost
   silently. `unpack_singleton=False` returns everything. *(observed)*
3. **`count_missing` returns a bool, not a count.** `_func_missing` wraps the result
   in `bool(...)`, so `np.count_nonzero` collapses to `True`/`False`, and the method
   is functionally identical to `any_missing` — the same answer by a longer route.
   Annotated `-> int`. *(observed)*
4. **`where_missing(dates)` reports the wrong periods.** The mask is computed on the
   requested data but zipped against `self.span`, so the periods returned are
   counted from the series start rather than from the request. On a series starting
   2020Q1 with a hole at 2020Q4, `where_missing(Span(qq(2020,3), qq(2021,1)))`
   returns `(qq(2020,2),)`. *(observed)* The no-argument form is correct.
5. **`shrink_num_variants(n)` with `n` equal to the current count empties every
   column.** `remove` is 0 and `self.data[:, :-remove]` is `self.data[:, :0]`,
   giving shape `(n, 0)`. *(observed)* `alter_num_variants` never reaches this case.
6. **`iter_variants` is broken twice over.** `iter_own_data_variants_from_until`
   yields the rows of `data.T`, which are one-dimensional, and `_replace_data` then
   calls `trim`, which indexes `axis=1`, so both single- and multi-variant series
   raise `numpy.exceptions.AxisError: axis 1 is out of bounds for array of dimension
   1`. *(observed)* Behind that fault sits a second one: the loop runs over
   `iter_data_variants_from_until`, which is wrapped in `exhaust_then_last` and
   never terminates. Repairing the shape alone would turn the crash into an endless
   generator, so both need fixing together.
7. **`clip` fails badly at two edges.** On an empty series the comparison against a
   `None` start raises `wrongdoings.Error: Cannot handle periods of different time
   frequencies in this context`. Clipped to a span lying entirely outside the
   series it leaves an object with no data whose `start` is later than its `end`
   (2020 series clipped to 2021Q1-2021Q2 came back with `start` 2021Q1 and `end`
   2020Q4). *(observed)*
8. **`data_type=int` produces a series that cannot be read.** Any padding path calls
   `_np.pad(..., constant_values=_np.nan)` in `_create_expanded_data`, so a plain
   `get_data()` raises `ValueError: cannot convert float NaN to integer`.
   *(observed)*

### Docs vs code

1. `Series.__init__` silently trims. `_from_start_and_values` ends with
   `self.trim()`, stripping leading and trailing missing rows at construction. The
   constructor docstring does not mention it. This is why a leading-gap series
   cannot be built directly. The `periods=` path trims too, through `set_data`.
2. The constructor docstring documents only `start`, `periods`, `values` and `func`.
   `num_variants`, `data_type`, `description`, `frequency` and `populate` are all in
   the signature and none appear. `frequency` is accepted by all three populators
   and read by none of them.
3. `from_start_and_array`'s docstring does not say that the array is not copied. The
   series keeps the caller's array, so later writes to it change the series.
   *(observed)*
4. Five annotations disagree with the code: `alter_num_variants` and `logistic` are
   `-> Self` and return `None`; `trim` is `-> None` and returns `self`;
   `get_data_and_periods` is `-> _np.ndarray` and returns a `(data, periods)` tuple;
   `_shift_eopy` is `-> Self` and returns `None`.
5. `clip`'s docstring explains `None` for either end but not that a `new_start`
   earlier than the current start, or a `new_end` later than the current end, is
   silently ignored — the method only ever shortens.
6. Copy-paste slips in the operator docstrings, left in place: `__mul__` says
   "self + other", `__rmul__` "other + self", `__truediv__` says "self - other",
   `__rtruediv__` "other - self".

### Notes

1. Constructor signature settled: `Series.__init__` is keyword-only, and
   `_SERIES_POPULATOR[(True, False, True, False)] = _from_start_and_values` confirms
   that `start=` plus `values=` is a supported combination. `start_date=` and
   `dates=` are accepted as legacy aliases, which is why `_hp.hpf` can build its
   results with `start_date=`.
2. The two constructors differ over whether they copy the caller's array.
   `_from_start_and_values` ends with `values.astype(self.data_type)`, which copies
   even when the type already matches, so the constructor is safe;
   `from_start_and_array` assigns the reshaped array straight through and shares it.
   Only the second needs the warning, and only the second block carries one.
   *(observed)* both ways.
3. `Iterator` is used in three annotations (`iter_variants`,
   `iter_own_data_variants_from_until`, `iter_data_variants_from_until`) and never
   imported; only `Iterable` and `Callable` are. Survives on
   `from __future__ import annotations`.
4. `_check_data_shape` is defined and called nowhere in the package.
5. `range = span` shadows the builtin inside the class body. Nothing in the class
   body after that line uses `range`, and the uses inside method bodies resolve to
   the builtin at call time, so this is latent only.
6. `reset` erases the description, because it rebuilds the object through the
   constructor whose default is `""`. `trim` calls `reset` when every observation is
   missing, so an all-missing series loses its description too. *(observed)*
7. `empty()` keeps `start` and the description. With no rows behind it, `end`
   reports the period *before* `start` and `span` comes back backwards
   (`Span(qq(2020,1), qq(2019,4))`). *(observed)*
8. `hstack` drops descriptions; the result always has `""`. *(observed)*
9. `get_data_variant` and `get_data_variant_from_until` fall back to variant 0 when
   the index is not below the number of variants (`variant if variant and
   variant < self.data.shape[1] else 0`), so a mistyped index returns the wrong
   column rather than raising. Negative indices pass through to numpy and count from
   the right. *(observed)*
10. `get_data_from_until` given a reversed pair returns an empty array rather than
    raising. *(observed)*
11. `iter_own_data_variants_from_until(...)` yields views onto the series' own data,
    so writing into a yielded array changes the series; with an explicit
    `from_until` it yields fresh copies. *(observed)* This is the other half of the
    `arip.py` note 4 finding, which tested only the explicit-`from_until` path; the
    two agree. `iter_data_variants_from_until` wraps the same iterator in
    `exhaust_then_last`, so it never stops — `list()` over it hangs. *(observed)*
12. The `_start` property (`call_name="start"`) raises `NotImplementedError` and
    exists only to carry a documentation entry; `start` is an ordinary slot
    attribute, the property never runs because the attribute shadows it, and
    assigning to the attribute retimes the series. It is documented under the name
    `start`, since that is what appears in the generated reference.
13. `set_start`, and assignment to `start`, do not check the frequency of the new
    period against the periods already in the series.
14. FIXME comments left in place: `__pow__` on `1 ** nan` and the empty encompassing
    span in `_binop`.
15. The comment block above `__all__`, "The following functions can return either a
    new time series object ... or a scalar", names no functions.

### Could not verify

None. Every example in the new blocks was run against the installed package
(`documark`, `scipy`, `plotly`, `daqp`) and all 233 of them pass as doctests.
