# Bug Log — `datapie/src/datapie/databoxes`

Compiled with AI assistance while documenting this folder. I am new to the
codebase and have not tried to judge which findings are intentional design and
which are defects; everything observed is recorded, and a review from someone
who knows the module would be welcome.

Findings are anchored on method and function names, not line numbers. Items
marked *(observed)* were confirmed by running the code; everything else follows
from reading it.

**No source changes were made in this folder.** Everything is docstrings plus
`add_heading=False` on decorators that already carried `@_dm.reference`.

`_imports2.py` and `_imports3.py` are undocumented on purpose — see their block.

---

## `_exports.py`

### Bugs

1. **An empty export destroys the target file.** `to_csv_file` calls
   `_catch_empty` and then opens `file_name` with `"w+"` whatever that check
   decided, so with the default `when_empty="warning"` a databox holding no time
   series truncates whatever was at that path and leaves a file of zero length.
   *(observed)* — a file containing text came back as `''`, with only a warning
   printed. `when_empty="error"` raises before the `open` and leaves the file
   untouched. *(observed)*
2. **`frequency` is dead.** It is in the signature of `to_csv_file` and no line
   of the body reads it. On a databox holding quarterly and monthly series,
   `to_csv_file(frequency=Frequency.QUARTERLY)` still wrote the monthly block.
   *(observed)* `frequency_span` and `span` are the arguments that do this.
3. **`description_heading` is dead.** The heading of the description row comes
   from the module constant `_DESCRIPTION_ROW_HEADING` inside
   `_ExportBlock.__iter__`. `description_heading="MY_HEADING"` produced a row
   headed `__description__`. *(observed)*
4. **`numeric_format` is dead.** It is carried into `_ExportBlock` and never
   read there; values reach `csv.writer` as Python floats.
   `numeric_format="0.2f"` wrote `1.234567890123`. *(observed)* Only `round`
   affects output precision.
5. **`_get_names_to_export` cannot run.** Its first line reads
   `self.get_series_names_by_frequency(frequency)` while the parameter is named
   `databox`, so any call raises `NameError`. Nothing calls it, so it is dead as
   well as broken.
6. **`span=[]` raises instead of reporting an empty export.**
   `_resolve_frequency_span` reads `span[0].frequency` before `_catch_empty`
   runs, so an empty span gives `IndexError: tuple index out of range` and
   `when_empty` has no say. *(observed)* with both `"warning"` and `"silent"`.

### Notes

1. `csv_writer_settings` cannot carry `delimiter` or `lineterminator`. Both are
   already passed explicitly to `csv.writer`, so either raises `TypeError:
   _csv.writer() got multiple values for keyword argument`. *(observed)* A
   quoting rule goes through fine.
2. Entries that are not time series are skipped in silence and never appear in
   `names_exported`. *(observed)*
3. Names in `names` that the databox does not hold are dropped without
   complaint, because `shallow` is called without `strict_names=True`. `names`
   also fixes the column order. *(observed)*
4. `round` defaults to 12, not to `None`, so output is rounded even when nothing
   was asked for. `1/3` wrote as `0.333333333333` by default and
   `0.3333333333333333` with `round=None`. *(observed)*
5. `date_formatter` defaults to `_DEFAULT_DATE_FORMATTER`, which is `str`. For
   quarterly and monthly periods that matches the SDMX form; integer-indexed
   periods come out as `(1)`, `(2)`. *(observed)*
6. An empty series has `UNKNOWN` frequency and is written as a header-only
   block, `__unknown__,e,` with no data rows. *(observed)*
7. A `span` whose frequency matches no series warns "No data exported" and
   writes an empty file — bug 1 applies. *(observed)*
8. `to_sheet`, `to_csv` and `to_pickle` have no callers inside the package.
   `to_sheet` carries `@_dm.no_reference`; `to_csv` and `to_pickle` carry no
   decorator at all.
9. `to_csv_file` layout confirmed: one block of columns per frequency side by
   side, each ending in an empty separator column, shorter blocks padded with
   empty rows; a multi-variant series takes one column per variant and heads the
   extras with `*`. *(observed)*
10. `Literal` is used in two annotations and never imported — `when_empty` in
    `to_csv_file` and the same parameter of `_catch_empty`.

---

## `_imports.py`

### Bugs

1. **A CSV written with any separator other than a comma cannot be read back.**
   `from_csv_file`'s `delimiter` reaches only the numeric reader
   (`_read_array_for_block` → `numpy.genfromtxt`). The reader that splits the
   heading rows, `_read_csv`, declares `delimiter=","` as a parameter of its own
   and never forwards it to `csv.reader`, so headings are always split on
   commas. Routing it through `csv_reader_settings={"delimiter": ";"}` does not
   help either: that keyword lands on the same parameter and is absorbed. A file
   written by `to_csv_file(delimiter=";")` comes back as `ValueError: invalid
   literal for int() with base 10: '1;1.0;'` — the whole heading line arrives as
   one cell, is still recognised as a frequency mark, and the period parser
   chokes on the joined data line. *(observed)* The one way through is a
   registered `csv` dialect: `delimiter=";"` for the numbers plus
   `csv_reader_settings={"dialect": ...}` for the headings. *(observed)*
2. **`start_date_only` is silently ignored.** `_resolve_legacy_option`
   substitutes the legacy value only when the new option `is None`, and
   `start_period_only` defaults to `False`, so the condition never holds.
   `from_csv_file(start_date_only=True)` behaves as `False` and issues no
   deprecation warning. *(observed)* `date_creator` does work and does warn,
   because `period_from_string` defaults to `None`. *(observed)* Contrast
   `merge_strategy` in `_merge.py` note 2 — the same legacy pattern, written the
   same way round, but guarding on a parameter with a real default, so it fires.
3. **A `description_row` that does not match the file destroys data silently.**
   Nothing checks the flag against the file. Set on a file with no description
   row, the first data row is consumed as headings: its numbers become the
   descriptions and its observations are lost. A three-line file
   `__quarterly__,x,` / `2020-Q1,1.0,` / `2020-Q2,2.0,` read with
   `description_row=True` gave a one-observation series `[[2.0]]` carrying the
   description `'1.0'`. *(observed)* The opposite mistake at least fails, though
   obscurely, with `ValueError: not enough values to unpack (expected 2, got
   1)`. *(observed)*
4. **Every field default in `_ImportBlock` is a tuple.** Each dataclass line
   ends with a trailing comma — `row_index: Iterable[int] | None = None,` — so
   the default is `(None,)`, not `None`. `_ImportBlock().row_index` is
   `(None,)`. *(observed)* Harmless today, since the only construction site
   passes all six fields positionally.
5. **The two `__`-marked conventions of the file format collide.** `_is_start`
   accepts any name-row cell beginning `__` whose next letter starts a frequency
   name, and `Frequency.from_letter("__description__")` returns `DAILY`.
   *(observed)* So the mark that opens a block, `__quarterly__`, and the heading
   of the description row, `__description__`, are indistinguishable to the
   scanner: a `__description__` cell reaching a name row opens a daily block.
   `to_csv_file` never puts it there, so the two do not meet today, but nothing
   enforces the separation and any user-written column name of that shape has
   the same effect.

### Notes

1. `numpy_reader_settings` cannot carry `delimiter`, `skip_header` or `usecols`.
   All three are already supplied to `genfromtxt`, so each raises `TypeError`.
   Other settings such as `comments` and `missing_values` pass through.
   *(observed)*
2. `databox_settings` is not settings. It is unpacked into the `Databox`
   constructor, which forwards to `dict`, so `databox_settings={"note": 1}` puts
   an entry called `note` into the new databox rather than configuring anything.
   *(observed)*
3. A blank date cell is treated differently by the two modes of
   `start_period_only`. Left alone, the row is skipped and its numbers dropped;
   set to `True`, no row is skipped and those numbers are kept. On `2020-Q1,1.0`
   / `,9.0` / `2020-Q3,3.0` the default gave `[1.0, nan, 3.0]` and
   `start_period_only=True` gave `[1.0, 9.0, 3.0]`. *(observed)*
4. `name_row_transform` is applied to every cell of the name row, frequency
   marks included. `str.upper` is safe; a transform that strips leading
   underscores would stop the blocks being recognised. *(observed)*
5. In `from_csv_file`, two columns carrying the same name give one entry, the
   right-hand one; the earlier series is replaced without a word. *(observed)*
6. A file with no rows, and a file whose first row holds no frequency mark, both
   give an empty databox with no warning. A missing file raises
   `FileNotFoundError`. *(observed)*
7. `from_pickle_file` returns whatever the file holds and never checks it is a
   databox. A pickle of `[1, 2, 3]` came back as a list, despite the `-> Self`
   annotation. *(observed)*
8. `_block_iterator` mutates its argument: `name_row += ["__"]` appends the
   sentinel to the caller's list, which is `header_rows[0]`. Repeated calls to
   `from_csv_file` are unaffected, since the file is read afresh each time, but
   a list reused across two calls to the helper collects a sentinel per pass.
   *(observed)*
9. Round trip against `to_csv_file` confirmed: names, descriptions, missing
   values, a two-variant series written as a `*` column, and quarterly and
   monthly blocks side by side all came back equal under `same_as`. *(observed)*
10. `from_sheet`, `from_csv` and `from_pickle` have no callers inside the
    package. `from_sheet` carries `@_dm.no_reference`; `from_csv` and
    `from_pickle` carry no decorator at all.
11. **The two constructors are decorated inconsistently.** `from_pickle_file`
    carries no `call_name`, while `from_csv_file` has
    `call_name="Databox.from_csv_file"`, so the reference lists one as
    `Databox.from_csv_file` and the other as a bare `from_pickle_file`. The
    categories differ too — `"constructor"` against `"import_export"` — although
    both build a new `Databox`.
12. `encoding` as a `pickle.load` argument is the one documented claim in this
    file taken from the standard library's documentation rather than exercised
    here.

---

## `_jsonables.py`

### Bugs

1. **The two reader `call_name` values are misspelled** —
   `Databox.seres_from_jsonable` and `Databox.seres_from_json_file`, missing the
   `i` of "series". They set the page anchors, so the `##` headings in the
   docstrings carry the misspelling too: documark builds the index link from
   `call_name` and the section anchor from the heading, and spelling one
   correctly while the other stays wrong leaves two dead links on the generated
   page. *(observed)* Fixing `call_name` would let both be spelled properly but
   changes the published anchor.
2. **A single multi-variant series makes the whole databox unwritable.**
   `series_to_jsonable` calls `Series.to_jsonable` per entry, which raises
   `ValueError: The series has multiple variants. Set
   allow_multiple_variants=True to serialize`; passing that flag raises
   `NotImplementedError: 'allow_multiple_variants=True is not implemented yet.'`
   *(observed)* both ways. Inherited from `series/_jsonables.py` bug 1, but at
   databox level one such series stops every other series being written too.
3. **Missing observations are written as bare `NaN`, which is not valid JSON.**
   *(observed)*: a series holding `nan` writes `NaN,` into the file. Python's
   own `json` reads it back without complaint, and so does
   `series_from_json_file`, so the round trip inside this package is clean.

   The claim that another language would reject it is **not directly tested**.
   What was observed is a Python-side proxy: `json.load` with a `parse_constant`
   hook fires on the `NaN` token. That `NaN` is outside RFC 8259 is a fact about
   the specification, not something measured here — no non-Python reader was
   run.
4. **`json_dump_settings={}` does not give compact output.** The body is
   `json_dump_settings or {"indent": 4}`, and an empty dictionary is falsy, so
   it falls through to the indented default. *(observed)*: `{}` produced a
   169-byte indented file, `{"indent": 0}` a 97-byte one. Passing `{}` looks
   like "no settings" and silently means "the default".

### Notes

1. **Entries that are not time series are dropped in silence.** The
   comprehension in `series_to_jsonable` filters on `isinstance(value, Series)`,
   so a round trip through JSON quietly loses everything else the databox held.
   *(observed)*
2. `json_load_settings` on `series_from_json_file` is **not** keyword-only,
   while `json_dump_settings` on `series_to_json_file` is. So the reader accepts
   it positionally and the writer does not. *(observed)*
3. The `include_frequency` / `frequency_included` asymmetry from
   `series/_jsonables.py` propagates here unchanged: writing with
   `include_frequency=False` and reading with the defaults raises `KeyError:
   'frequency'`. *(observed)*
4. Round trip verified: names, values, descriptions and missing observations
   come back equal under `same_as`, through both the dictionary pair and the
   file pair. *(observed)*
5. The two readers are `category="constructor"` while the two writers are
   `category="import_export"`, so the four appear under two different headings
   despite being two pairs. Same split as `_imports.py` note 11.
6. The `_jsonables.py` module docstring is empty.

---

## `_merge.py`

### Bugs

None.

### Notes

1. **Twelve strategies exist; the docstring long listed only seven.**
   `_MERGE_STRATEGY_DISPATCH` has twelve keys. `hstack` is deliberately excluded
   — the `MergeStrategyType` alias annotates it `# Legacy alias for stack, do
   not include in the docstring`. The other four, `overlay_by_observation`,
   `overlay_by_span`, `underlay_by_observation` and `underlay_by_span`, carry no
   such marker and work, doing four genuinely different things. *(observed)* on
   a databox pair whose series was `[1, 2, nan, 4]` against `[9, 9, 9, 9]`: the
   two overlay forms gave `[9, 9, 9, 9]`, `underlay_by_span` gave `[1, 2, nan,
   4]`, and `underlay_by_observation` gave `[1, 2, 9, 4]`, filling the gap alone
   — the only strategy that fills gaps from a second databox.

   They have a silent edge: `_merge_lay` acts only when **both** values are
   `Series`, so for any other type the four fall through and keep the original,
   behaving as `discard` without saying so. *(observed)* on plain integers.
2. **`merge_strategy` is a legacy argument that works.** The body reads `if
   merge_strategy is not None: strategy = merge_strategy`, and since `strategy`
   has a real default the substitution fires whenever the legacy name is passed.
   *(observed)* The contrast case to `_imports.py` bug 2, written the same way
   round but guarding on a parameter defaulting to `False`, so it can never
   fire. Neither issues a deprecation warning.
3. **`"discard"` and `"silent"` reach the same outcome by different paths.**
   `_merge_discard` is a bare `pass`; `"silent"` maps to `_merge_report`, which
   calls `stream.add(key)`. They converge because `create_stream(strategy, ...,
   when_no_stream="silent")` falls back to a `SilentStream` for `"discard"` —
   `"discard"` is not a key of `STREAM_FACTORY` — and a `SilentStream` swallows
   whatever is added. *(observed)*: both left the original value in place and
   emitted no warning. Redundant rather than wrong, but a future change to
   `SilentStream` would separate them.
4. All twelve strategies confirmed end to end. `stack` and `hstack` are
   identical; `replace` takes the new value; `warning` behaves as `discard` and
   emits one warning per duplicate key; `error` and `critical` raise
   `wrongdoings.Error` and `wrongdoings.Critical` naming the duplicate key.
   *(observed)*
5. `by_merging` is a public classmethod carrying no decorator, so it does not
   reach the rendered page.

---

## `_views.py`

Every function here is private and `__all__` is empty. It is the display
machinery behind a databox's `repr`.

**Two different modules are called "views", and this file uses both names.** The
class is `class Mixin(_views.Mixin, )`, where `_views` is bound by `from ..
import views as _views` — the *package-level* `datapie/views.py`, not this file.
Anyone reading `_views.` inside `databoxes/_views.py` is looking at the other
module. `series/_views.py` specialises the same base.

### Bugs

1. **`_get_short_row_` raises `NameError`.** The return line is

       return _REPR_INDENT + _views._VERTICAL_ELLIPSIS.rjust(max_len) + " "*len(_REPR_SEPARATOR) + _VERTICAL_ELLIPSIS

   — the same constant twice, qualified the first time and bare the second. The
   bare one is not imported and does not exist in this module, so the call
   raises `NameError: name '_VERTICAL_ELLIPSIS' is not defined`. *(observed)*
   `series/_views.py` has the same method and qualifies both occurrences, so
   this file is the odd one out.

   **It is masked by a second fault one level up.** `_get_short_row_` is reached
   only from `views.Mixin.__invert__`, the `~db` short view, and that method
   tests `len(content_view) > 2*_SHORT_ROWS` while `datapie/views.py` defines
   `_SHORT_ROWS_` with a trailing underscore. So `~db` raises `NameError: name
   '_SHORT_ROWS' is not defined` before the short row is ever built, for a
   databox of any size. *(observed)* on both a 1-item and a 20-item databox.
   Fixing `views.py` would expose this one; they should be fixed together.
   Ordinary `repr(db)` goes through neither path and works.
2. **`_get_key_repr` annotates `key: Any` and `Any` is never imported.**
   Harmless at runtime because of `from __future__ import annotations`, but
   `typing.get_type_hints` on it raises `NameError: name 'Any' is not defined`.
   *(observed)*

---

## `main.py`

### Bugs

1. **`Databox.from_array` does not work at all, and prints to standard output.**
   The helper it delegates to, `_from_horizontal_array_and_constructor`, has its
   only working line commented out and a debug `print` in its place:

       for name, values, description in zip(names, array, descriptions, ):
           print(name, type(values), description, )
           # self[name] = series_constructor(values=values, description=description, )

   So the loop prints one line per name and assigns nothing. *(observed)*:
   `Databox.from_array(a, ["x","y"], start=qq(2020,1))` printed `x <class
   'numpy.ndarray'>` and `y <class 'numpy.ndarray'>` and returned a databox with
   **no keys**. With `target_db=` supplied it returns that databox unchanged. A
   public constructor that silently produces nothing and writes to stdout.

   **Dead path.** A grep over `src/datapie` finds no caller, which is presumably
   how a commented-out line and a stray `print` survived.
2. **`evaluate_expression` cannot evaluate any expression containing `=`.**
   `_reformat_eval_expression` reads

       lhs, *rhs = expression.split(expression, "=", )

   — the string is split **by itself**, and `"="` is passed where `str.split`
   expects a maximum split count, so the call raises `TypeError: 'str' object
   cannot be interpreted as an integer`. *(observed)*

   **The blast radius is the `=` character, not assignment.** The guard above it
   is only `if "=" in expression`. *(observed)*, failing: `a=b`, `a==b`, `a<=b`,
   `x = y + 1`, any call using a keyword argument such as `round(a, ndigits=2)`,
   and any default argument such as `(lambda x=1: x)(2)`. *(observed)*, passing:
   `a+b`, `round(a, 2)`, `a.get_data()`, `[x for x in (1,2)]` and `{'k': 1}` —
   dict literals survive because they use `:` rather than `=`. So no comparison
   can be evaluated, and no keyword argument can be passed to any function
   inside an expression. Fails identically through the `__call__` shortcut,
   `db("a=b")`.

   **A second fault waits behind it:** the next line is `expression =
   "({lhs})-({rhs})"`, which is not an f-string, so even once the split is
   repaired the function would return that literal text. Both need fixing
   together.

   **This one is on a live path.** `chartpacks/main.py` calls
   `input_db.evaluate_expression(self.expression, series_function_context=True,
   context=context, )` for every chart drawn, and `self.expression` is the
   user's own chart string. So any chartpack whose expression carries a keyword
   argument or a comparison fails at plot time with a `TypeError` naming neither
   the chart nor the expression.
3. **`validate`'s annotation contradicts its body, and the annotated usage
   crashes.** The parameter is annotated `validators: dict[str, Callable] |
   None`, but the body reads `validators[key][0]` and `validators[key][1]`, so
   each value has to be a *sequence* of `(func, message)`. Passing what the
   annotation asks for raises `TypeError: 'function' object is not
   subscriptable`. *(observed)* The working forms are `{"n": (func,)}` and
   `{"n": (func, "message")}`. *(observed)*
4. **`apply`'s `in_place` defaults to discarding the result.** The body is
   `output = func(self[s])` followed by `if not in_place: self[s] = output`, so
   with the default `in_place=True` the return value is thrown away and only
   side effects on the object survive. `db.apply(lambda s: s*2)` does nothing at
   all to a databox of series — *(observed)* — while `in_place=False` doubles
   them. *(observed)* The sense of the name is inverted from what a reader
   expects.

### Notes

1. `copy(source_names, target_names)` does not duplicate the databox; it returns
   a **new databox holding only the copied names**. `copy(["a"], ["c"])` gave a
   databox whose only key is `c`. *(observed)* `shallow(["a"])` likewise returns
   a databox holding just `a`. Both names invite the opposite reading. `copy` is
   genuinely deep — the series objects differ and writes do not leak — while
   `shallow` shares them. *(observed)* both ways.
2. **A callable means different things in `rename`'s two positions.** A callable
   in `source_names` *selects*; a callable in `target_names` *renames*. So
   `rename(lambda n: n.upper())` renames nothing — it selects every name and
   supplies no new one. *(observed)*
3. The four `overlay_`/`underlay_` methods pass `**kwargs` through to `_lay` and
   act only on series: an entry present in both databoxes but not a series is
   left alone. *(observed)* Their per-series behaviour matches the `Series`
   methods of the same name.
4. `steady` and `zero` are classmethods whose first parameter is
   `steady_databoxable`, not a databox. `zero` rejects `deviation` outright —
   passing it at all, `True` or `False`, raises `ValueError: The 'deviation'
   argument is not allowed for the Databox.zero method`. *(observed)* Their
   pass-through arguments `unpack_single`, `prepend_initial` and
   `append_terminal` were not exercised, no suitable model object being
   available.
5. `get_names` carries a legacy `filter` argument alongside `test`, marked in
   the signature for deprecation. It shadows the builtin inside the method, and
   it is a different thing from the public `Databox.filter` method.
6. Verified working: `get_names`, `get_missing_names`, `num_items`, `to_dict`,
   `filter`, `get_series_names_by_frequency`, `get_span_by_frequency`,
   `array_from_series` (which takes `names` *and* `periods`, both required),
   `rename`, `remove`, `keep`, `generate`, `clip_series`, `evaluate_expression`
   (`"a+b"` on two series gave `[4.0, 6.0]`), `prepend` and `minus_control`.
   *(observed)*

---

## `_imports2.py` and `_imports3.py`

**Neither file is documented, and neither is reachable.** `Databox` inherits
`_merge.Mixin`, `_exports.Mixin`, `_imports.Mixin`, `_jsonables.Mixin`,
`_views.Mixin`, `_descriptions.Mixin` and `dict`, and `databoxes/main.py`
imports only `_imports` and `_exports`. A search of the whole `src` tree finds
no reference to either module, to `read_csv`, or to `Inlay` outside the two
files themselves. Both do import cleanly on their own.

### `_imports3.py`

A cosmetic rework of `_imports.py`, not a fix. Compared function by function on
the parsed body of each — same set of functions, none added, none removed, every
body identical apart from `/` markers on two nested helpers. It renames `class
Mixin` to `class Inlay`, adds positional-only `/` markers in seven places,
indents the docstring bodies under their `???+ input` markers, and collapses one
conditional onto a single line. The only change with a behavioural consequence
is the `/` in `from_pickle_file(klass, file_name, /, **kwargs)`:
`from_pickle_file(file_name="x.pkl")` works in `_imports.py` and raises
`TypeError` here.

**Every bug listed under `_imports.py` is present here verbatim.** If this file
is meant to replace `_imports.py`, the bugs travel with it.

### `_imports2.py`

A different and unfinished experiment. It shares no function with `_imports.py`
except `_remove_nonascii_from_start`. It offers a module-level
`read_csv(file_path, **kwargs)` built on a `_SheetFileFactory` protocol, a
`_ColumnwiseFileFactory` and a `_Block` class, none of which appear in the other
two files. It carries its own `# FIXME: Make read_csv a class method`.

**It does not do what its name says.** `_Block.create_databox_from_block` is
annotated `-> Databox` and returns `self._data_array`, a numpy array.
*(observed)* on a one-series file, `read_csv` returned `(array([[nan, 1.], [nan,
2.]]),)` — a tuple of arrays, date column read as `nan`, no `Databox` anywhere.
The names and descriptions gathered by `_Block.add_header` are never used.

Worth a decision on whether either file is being kept.
