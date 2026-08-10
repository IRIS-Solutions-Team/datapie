# Bug / Documentation Log — `datapie/src/datapie/databoxes`

This log was compiled with AI assistance during the documentation rewrite. As I am
new to the codebase, I have not attempted to judge which findings are intentional
design and which are defects — everything observed is recorded here, and I would
welcome a review from someone who knows the module.

Findings are anchored on method and function names rather than line numbers, since
inserting the documentation blocks shifts every line in the file. Items marked
*(observed)* were confirmed by running the code; everything else follows from
reading it.

**Scope:** one block per file in the `databoxes` folder. Every block has the same
three sections, in the same order:

| Section | Contents |
| ------- | -------- |
| **Bugs** | The code does the wrong thing, or crashes. |
| **Notes** | Verified behaviour, dead code, style, open questions. |
| **Docs vs code** | The docstring and the code disagree; typos. |

---

## `_exports.py`

### Bugs

1. **An empty export destroys the target file.** `to_csv_file` calls `_catch_empty`
   and then opens `file_name` with `"w+"` whatever that check decided, so with the
   default `when_empty="warning"` a databox holding no time series truncates
   whatever was at that path and leaves a file of zero length. *(observed)* — a file
   containing text came back as `''` after the call, with only a warning printed.
   `when_empty="error"` raises before the `open` and leaves the file untouched.
   *(observed)*
2. **`frequency` is dead.** It is in the signature of `to_csv_file` and no line of
   the body reads it. On a databox holding quarterly and monthly series,
   `to_csv_file(frequency=Frequency.QUARTERLY)` still wrote the monthly block.
   *(observed)* `frequency_span` and `span` are the arguments that do this.
3. **`description_heading` is dead.** It is in the signature, but the heading of the
   description row comes from the module constant `_DESCRIPTION_ROW_HEADING` inside
   `_ExportBlock.__iter__`. `description_heading="MY_HEADING"` produced a row headed
   `__description__`. *(observed)*
4. **`numeric_format` is dead.** It is carried into `_ExportBlock` and never read
   there; values reach `csv.writer` as Python floats and are written in Python's own
   text form. `numeric_format="0.2f"` wrote `1.234567890123`. *(observed)* Only
   `round` affects the precision of the output.
5. **`_get_names_to_export` cannot run.** Its first line is
   `names_from_databox = self.get_series_names_by_frequency(frequency)` while the
   parameter is named `databox`, so any call raises `NameError`. Nothing in the
   package calls it, so it is dead as well as broken.
6. **`span=[]` raises instead of reporting an empty export.** `_resolve_frequency_span`
   reads `span[0].frequency` before `_catch_empty` runs, so an empty span gives
   `IndexError: tuple index out of range` and `when_empty` has no say. *(observed)*
   with both `"warning"` and `"silent"`.

### Notes

1. `csv_writer_settings` cannot carry `delimiter` or `lineterminator`. Both are
   already passed explicitly to `csv.writer`, so either one raises
   `TypeError: _csv.writer() got multiple values for keyword argument`. *(observed)*
   A quoting rule goes through fine.
2. Entries that are not time series are skipped in silence and never appear in
   `names_exported`. *(observed)*
3. Names in `names` that the databox does not hold are dropped without complaint,
   because `shallow` is called without `strict_names=True`. `names` also fixes the
   column order; left alone, the databox's own order is used. *(observed)*
4. `round` defaults to 12, not to `None`, so output is rounded even when nothing was
   asked for. `1/3` wrote as `0.333333333333` by default and
   `0.3333333333333333` with `round=None`. *(observed)*
5. `date_formatter` defaults to the module constant `_DEFAULT_DATE_FORMATTER`, which
   is `str`. For quarterly and monthly periods that matches the SDMX form the
   docstring promises; integer-indexed periods come out as `(1)`, `(2)`.
   *(observed)*
6. An empty series has `UNKNOWN` frequency and is written as a header-only block,
   `__unknown__,e,` with no data rows. *(observed)*
7. A `span` whose frequency matches no series in the databox warns "No data
   exported" and writes an empty file — bug 1 applies. *(observed)*
8. `to_sheet`, `to_csv` and `to_pickle` have no callers inside the package.
   `to_sheet` carries `@_dm.no_reference`, so it is kept out of the generated
   documentation; `to_csv` and `to_pickle` carry no decorator at all.
9. Layout confirmed: one block of columns per frequency side by side, each ending in
   an empty separator column, shorter blocks padded with empty rows; a multi-variant
   series takes one column per variant and heads the extras with `*`. *(observed)*
10. `Literal` is used in two annotations and never imported — `when_empty` in
    `to_csv_file`, and the same parameter of `_catch_empty`. Harmless at runtime
    because of `from __future__ import annotations`; `typing.get_type_hints` would
    fail.

### Docs vs code

1. The usage block shows `round=None`; the default is `_DEFAULT_ROUND`, which is 12.
2. The usage block and the Input arguments omit `span`, `description_heading` and
   `return_info`. `span` matters most — it overrides `frequency_span` and decides
   which single frequency is written.
3. Returns documents `info` as though it were always returned. The method returns
   `None` unless `return_info=True`, and is annotated `-> dict[str, Any]` either
   way.
4. The `date_formatter` entry says "If `None`, SDMX string formatter is used". The
   default is `str` — see note 5.
5. `frequency` and `numeric_format` are documented as working arguments; neither
   does anything (bugs 2 and 4). `description_heading` is not documented at all,
   which at least matches its effect.
6. `to_pickle_file`'s usage block writes `self.to_pickle(...)`, the alias, rather
   than the method's own name.
7. The `to_csv_file` docstring is the only one in the package whose `???+ input`
   descriptions sit at column zero rather than indented under the marker.

---

## `_imports.py`

### Bugs

1. **A CSV written with any separator other than a comma cannot be read back.**
   `from_csv_file`'s `delimiter` reaches only the numeric reader
   (`_read_array_for_block` → `numpy.genfromtxt`). The reader that splits the
   heading rows, `_read_csv`, declares `delimiter=","` as a parameter of its own and
   never forwards it to `csv.reader`, so the headings are always split on commas.
   Routing it through `csv_reader_settings={"delimiter": ";"}` does not help either:
   that keyword lands on the same parameter and is absorbed there. A file written by
   `to_csv_file(delimiter=";")` comes back as
   `ValueError: invalid literal for int() with base 10: '1;1.0;'` — the whole heading
   line arrives as one cell, is still recognised as a frequency mark, and the period
   parser then chokes on the joined data line. *(observed)* The one way through is a
   registered `csv` dialect: `delimiter=";"` for the numbers plus
   `csv_reader_settings={"dialect": ...}` for the headings, which reads the file
   correctly. *(observed)*
2. **`start_date_only` is silently ignored.** `_resolve_legacy_option` substitutes
   the legacy value only when the new option `is None`, and `start_period_only`
   defaults to `False`, so the condition never holds. `from_csv_file(start_date_only=True)`
   behaves as `False` and issues no deprecation warning at all. *(observed)*
   `date_creator` does work and does warn, because `period_from_string` defaults to
   `None`. *(observed)*
3. **A `description_row` that does not match the file destroys data silently.**
   Nothing checks the flag against the file. Set on a file that has no description
   row, the first data row is consumed as headings: its numbers become the
   descriptions and its observations are lost. A three-line file
   `__quarterly__,x,` / `2020-Q1,1.0,` / `2020-Q2,2.0,` read with
   `description_row=True` gave a one-observation series `[[2.0]]` carrying the
   description `'1.0'`. *(observed)* The opposite mistake at least fails, though
   obscurely, with `ValueError: not enough values to unpack (expected 2, got 1)`
   raised inside the period parser. *(observed)*
4. **Every field default in `_ImportBlock` is a tuple.** Each line of the dataclass
   ends with a trailing comma — `row_index: Iterable[int] | None = None,` — so the
   default is `(None,)`, not `None`. `_ImportBlock().row_index` is `(None,)`.
   *(observed)* Harmless today, since the only construction site passes all six
   fields positionally.

5. **The two `__`-marked conventions of the file format collide.** `_is_start`
   accepts any name-row cell that begins `__` and whose next letter starts the name
   of a frequency, and `Frequency.from_letter("__description__")` returns `DAILY`.
   *(observed)* So the mark that opens a block, `__quarterly__`, and the heading of
   the description row, `__description__`, are not distinguishable by the scanner: a
   `__description__` cell reaching a name row opens a daily block. `to_csv_file`
   never puts it there, so the two do not meet today, but nothing enforces the
   separation and any user-written column name of that shape has the same effect.
   `_is_start` passes only the first letter to `Frequency.from_letter` while the line
   setting `current_frequency` passes the whole cell; both work, since `from_letter`
   strips underscores and takes the first character.

### Notes

1. `numpy_reader_settings` cannot carry `delimiter`, `skip_header` or `usecols`. All
   three are already supplied to `genfromtxt`, so each raises `TypeError`. Other
   settings such as `comments` and `missing_values` pass through. *(observed)*
2. `databox_settings` is not settings. It is unpacked into the `Databox`
   constructor, which forwards to `dict`, so `databox_settings={"note": 1}` puts an
   entry called `note` into the new databox rather than configuring anything.
   *(observed)*
3. A blank date cell is treated differently by the two modes of `start_period_only`.
   Left alone, the row is skipped and its numbers are dropped; set to `True`, no row
   is skipped and those numbers are kept. On
   `2020-Q1,1.0` / `,9.0` / `2020-Q3,3.0` the default gave `[1.0, nan, 3.0]` and
   `start_period_only=True` gave `[1.0, 9.0, 3.0]`. *(observed)*
4. `name_row_transform` is applied to every cell of the name row, frequency marks
   included. `str.upper` is safe; a transform that strips leading underscores would
   stop the blocks being recognised. *(observed)*
5. Two columns carrying the same name give one entry, the right-hand one; the
   earlier series is replaced without a word. *(observed)*
6. A file with no rows, and a file whose first row holds no frequency mark, both give
   an empty databox with no warning. A missing file raises `FileNotFoundError`.
   *(observed)*
7. `from_pickle_file` returns whatever the file holds and never checks it is a
   databox. A pickle of `[1, 2, 3]` came back as a list, despite the `-> Self`
   annotation. *(observed)*
8. `_block_iterator` mutates its argument: `name_row += ["__"]` appends the sentinel
   to the caller's list, which is `header_rows[0]`, a row of the list `_read_csv`
   returned. Repeated calls to `from_csv_file` are unaffected, since the file is read
   afresh each time, but a list reused across two calls to the helper collects a
   sentinel per pass. *(observed)*
9. Round trip against `to_csv_file` confirmed: names, descriptions, missing values,
   a two-variant series written as a `*` column, and quarterly and monthly blocks
   side by side all came back equal under `same_as`. *(observed)*
10. `from_sheet`, `from_csv` and `from_pickle` have no callers inside the package.
    `from_sheet` carries `@_dm.no_reference`, so it is kept out of the generated
    documentation; `from_csv` and `from_pickle` carry no decorator at all.

### Docs vs code

1. `from_pickle_file` carries no `call_name`, while its sibling `from_csv_file` has
   `call_name="Databox.from_csv_file"`. Both are class methods, so the reference will
   list one as `Databox.from_csv_file` and the other as a bare `from_pickle_file`.
   The categories differ too — `"constructor"` against `"import_export"` — although
   both build a new `Databox`.
2. `databox_settings` is described as "Settings for the Databox constructor"; the
   entries end up as items in the databox (note 2). It is also missing from the
   usage block, though it is documented below it.
3. `delimiter` is described as "Character used to separate values in the CSV file",
   with no hint that it reaches only the numeric reader (bug 1).
4. Neither legacy argument, `date_creator` nor `start_date_only`, appears anywhere in
   the docstring, although both are in the signature and one of them warns when used.
5. `start_period_only` is described as inferring later periods "based on frequency",
   and says nothing about its more visible effect — that blank-dated rows stop being
   skipped (note 3).
6. Returns reads "An `Databox` populated with time series from the CSV file".
7. `from_pickle_file`'s usage block writes `self = Databox.from_pickle(...)`, the
   alias, rather than the method's own name. Same slip as `to_pickle_file` in
   `_exports.py`.
8. As in `_exports.py`, the `???+ input` descriptions sit at column zero rather than
   indented under their markers.

### Could not verify

All 20 examples pass as doctests, run in a scratch directory since they read and
write files. The one unexercised claim is `encoding` as a `pickle.load` argument,
taken from the standard library's documentation.

---

## `_imports2.py` and `_imports3.py`

**Neither file is documented.** Neither is reachable: `Databox` inherits
`_merge.Mixin`, `_exports.Mixin`, `_imports.Mixin`, `_jsonables.Mixin`,
`_views.Mixin`, `_descriptions.Mixin` and `dict`, and `databoxes/main.py` imports
only `_imports` and `_exports`. A search of the whole `src` tree finds no reference
to either module, to `read_csv`, or to `Inlay` outside the two files themselves.
Both do import cleanly on their own.

### `_imports3.py`

A cosmetic rework of `_imports.py`, not a fix. Compared function by function on the
parsed body of each — same set of functions, none added, none removed, and every body
identical apart from `/` markers on two nested helpers. It renames `class Mixin` to
`class Inlay`, adds positional-only `/` markers in seven places, indents the docstring
bodies under their `???+ input` markers (the one improvement, fixing `_imports.py`
docs-vs-code item 8), and collapses one conditional onto a single line. The only
change with a behavioural consequence is the `/` in
`from_pickle_file(klass, file_name, /, **kwargs)`: `from_pickle_file(file_name="x.pkl")`
works in `_imports.py` and raises `TypeError` here.

Every bug listed under `_imports.py` is present here verbatim: `_read_csv` still
declares `delimiter` and never forwards it, `_resolve_legacy_option` still cannot
fire for `start_period_only`, `_ImportBlock` still has trailing commas making each
default `(None,)`, nothing checks `description_row` against the file, and `_is_start`
still cannot tell a description-row heading from a frequency mark. If this
file is meant to replace `_imports.py`, the bugs travel with it.

### `_imports2.py`

A different and unfinished experiment, not a version of `_imports.py`. It shares no
function with it except `_remove_nonascii_from_start`. It offers a module-level
`read_csv(file_path, **kwargs)` built on a `_SheetFileFactory` protocol, a
`_ColumnwiseFileFactory` and a `_Block` class, none of which appear in the other two
files. It carries its own `# FIXME: Make read_csv a class method`.

It does not do what its name says. `_Block.create_databox_from_block` is annotated
`-> Databox` and returns `self._data_array`, a numpy array. *(observed)* on a
one-series file, `read_csv` returned `(array([[nan, 1.], [nan, 2.]]),)` — a tuple of
arrays, date column read as `nan`, no `Databox` anywhere. The names and descriptions
gathered by `_Block.add_header` are never used.

Documenting it would mean documenting an interface that does not yet work. Worth a
decision on whether it is being kept.
