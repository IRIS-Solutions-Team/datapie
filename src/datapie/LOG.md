# Bug Log — `datapie/src/datapie` (package root)

Compiled with AI assistance while documenting this folder. I am new to the
codebase and have not tried to judge which findings are intentional design and
which are defects; everything observed is recorded, and a review from someone
who knows the module would be welcome.

Findings are anchored on method and function names, not line numbers. Items
marked *(observed)* were confirmed by running the code; everything else follows
from reading it.

**In `periods.py`, docstrings were rewritten and `add_heading=False` was added
to 26 `_dm.reference` calls** — 21 decorator lines, plus the five calls applied
to the wrapped constructors at run time (`yy = _dm.reference(...)(yy)` and its
four siblings), which are not decorator lines. That flag is the only executable
change, and it is required: see "Docs vs code" 10. Fifty-two classes, methods
and functions had their docstrings replaced or added, and the five wrapped
constructors (`yy`, `hh`, `qq`, `mm`, `ii`) had their `__doc__ = ...`
assignments rewritten. Two entities have no docstring slot — `start`/`end` and
`PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION` are module-level assignments — so their
blocks stay as `#` comment blocks.

Docstrings whose existing text was already accurate were left as they stood in
substance; see "Docs vs code" 8. **One later pass edited nine of them anyway**,
to drop `self` from their `**Input arguments.**` lists — see "Docs vs code" 12.
So "left alone" now means "text not rewritten", not "byte-identical". Two
whitespace-only passes touched them: four paragraphs were rewrapped and trailing
whitespace was stripped from ten lines, to bring the file within 80 columns.
Every docstring's word stream and the code's AST were checked identical across
both.

**In `frequencies.py`, eight docstrings were rewritten and `add_heading=False`
was added to four decorators** — `from_letter`, `from_sdmx_string`, `letter` and
`is_regular`, the four that carry a new `##` heading. That flag is the only
executable change. Three blocks stay as `#` comment blocks because they have no
docstring slot: the one over the seven `Frequency.X.__doc__` assignments, which
describes the family rather than any one member, and the two over the
module-level `YEARLY = ...` and `SDMX_PATTERNS = ...` assignments.

---

## `periods.py`

**Status:** applied. All 22 documented examples run green as doctests.

The module holds two public families. `Period` is an abstract base with six
concrete subclasses, one per frequency, each of which is a single integer
`serial` plus a class-level frequency. `Span` is a start period, an end period
and a step. Around them sit the short constructors `yy`, `hh`, `qq`, `mm`, `dd`
and `ii`, a contextual-period mechanism for spans whose ends are not yet known,
and about fifteen module-level helpers.

### Bugs

1. **Three methods on `Period` call themselves.** `to_ymd`, `to_sdmx_string` and
   `to_compact_string` each have a body of `return self.to_x(...)` — a call to
   the very method being defined, not to a base or a subclass. On any class that
   overrides them this never runs. On any class that does not, it recurses until
   the stack gives out.

   `IntegerPeriod` is such a class: it defines `to_sdmx_string` and
   `to_compact_string` but no `to_ymd`. So `ii(4).to_ymd()` raises
   `RecursionError`, and so does everything routed through it — `to_iso_string`,
   `to_python_date` and `refrequent`. *(observed)* all four. A
   `NotImplementedError` would name the problem; a `RecursionError` names
   nothing.

2. **`DailyPeriod.to_year_segment` subtracts a date from an integer.** The line
   is

       boy_serial = _dt.date(_dt.date.fromordinal(self.serial).year, 1, 1)

   — a `date` where the next line needs that date's ordinal, the `.toordinal()`
   having been left off. `self.serial - boy_serial` then raises `TypeError:
   unsupported operand type(s) for -: 'int' and 'datetime.date'`. *(observed)*

   The method is not called from inside the class, so the failure surfaces
   through everything built on it: the `segment` and `period` properties, and
   `create_tty`, which is what `shift("tty")` uses. *(observed)* all four on
   `dd(2020,3,15)`. Daily periods are the only frequency where these do not
   work.

3. **`<<` between two periods builds a span that iterates to nothing, because it
   swaps the endpoints.** The pair reads

       def __rshift__(self, end, ):   return Span(self, end, 1)
       def __lshift__(self, start, ): return Span(start, self, -1)

   so `a >> b` gives `Span(a, b, 1)` -- left operand first -- while `a << b`
   gives `Span(b, a, -1)`, right operand first. The two are reversed with
   respect to each other, and **that swap, not the negative step, is what
   empties the range**; the step sign is exactly what the docstring promises.

   `qq(2020,4) << qq(2020,1)` therefore has `len` 0 and lists as `[]`, while the
   `Span(qq(2020,4), qq(2020,1), -1)` the docstring gives as its equivalent
   lists all four quarters. *(observed)* both.

   Silent rather than loud — a caller gets a `Span` object and an empty
   iteration, not an error. `__lshift__` and `__rlshift__` also disagree with
   each other about which operand is which: `q << None` gives `Span(<>.end, q,
   -1)` and `None << q` gives `Span(q, <>.start, -1)`. *(observed)*

4. **The frequency check in `Span.__init__` tests the arguments, not the
   endpoints.** `_check_periods(from_per, until_per)` runs on the values as
   passed, after `self._start` and `self._end` have already been resolved from
   them. Two strings are both of type `str`, so the check compares `str` with
   `str` and passes whatever the strings say.

   `Span("2020-Q1", "2020-05")` therefore builds a span with a quarterly start
   and a monthly end, and reports a length of 16165. *(observed)* The same two
   periods passed as objects raise `wrongdoings.Error` as intended. *(observed)*

5. **`HalfyearlyPeriod.get_month` raises `NameError`.** The body reads
   `month_resolution[position][per]`, and no name `month_resolution` exists
   anywhere in the module — the per-class table is `_MONTH_DAY_RESOLUTION`.
   *(observed)* Nothing inside the package calls it, so it is dead as well as
   broken; no other frequency has a `get_month` at all.

6. **`Span.__rsub__` names its parameter `ather` and its body uses `other`.**
   Calling it raises `NameError: name 'other' is not defined`. *(observed)*
   directly.

   It is unreachable through the operator, though, and for a second reason:
   `Period.__sub__` accepts anything, so `period - span` is claimed by the left
   operand and fails inside it with `TypeError: int() argument must be a string,
   a bytes-like object or a real number, not 'Span'` before `__rsub__` is ever
   consulted. *(observed)*

7. **`_period_tuple_from_string` passes its arguments the wrong way round on
   every branch.** Each call is of the form
   `periods_from_sdmx_strings(frequency, (start, end, ))` or
   `Period.from_sdmx_string(frequency, period_string)`, while both of those take
   the strings first and the frequency second.

   So the string path of the public `ensure_period_tuple` cannot work at all:
   `"2020-Q1"` raises `KeyError`, and both the range forms (`...`, `>>`) and the
   comma-separated list raise `TypeError: 'NoneType' object is not iterable`.
   *(observed)* all four. Only the iterable path of `ensure_period_tuple` is
   usable.

8. **`Span.__sub__` against a period stops one short.** It builds
   `range(self._start-offset, self._end-offset, self._step)`, while the
   `_serials` property that drives iteration builds the same range with
   `+_sign(step)` added to the stop. For a four-period span, `span - span.start`
   gives `range(0, 3)` — three values against four periods. *(observed)* The two
   are meant to line up and do not.

### Docs vs code

1. **`Period.shift` says it modifies in place and returns nothing; it does
   neither.** The docstring's Returns section reads "Returns no value; the time
   period is modified in place." The body returns `self + by` or a `create_*`
   result, and the original period is untouched — `qq(2020,1).shift(2)` returns
   `qq(2020,3)` and leaves `qq(2020,1)` as it was. *(observed)*

   The same entry documents `by` as an integer only. The body also accepts four
   string codes — `"yoy"`, `"boy"`/`"soy"`, `"eopy"` and `"tty"` — none of which
   appear in the docs. Two of them are worth knowing about: `"tty"` returns
   `None` rather than a period when `self` is in the first segment of its year
   *(observed)*, and any unrecognised string is not rejected but falls through
   to `self + by`, where `int()` raises `ValueError`. *(observed)*

2. **The `<<` shorthand is documented correctly and implemented backwards.** The
   `Span` constructor entry states that `end_per << start_per` is equivalent to
   `Span(end_per, start_per, step=-1)`. It is not; see bug 3.

3. **`from_iso_string` and `from_python_date` both promise a daily fallback that
   does not exist.** Each documents `frequency` as "if `None`, a time period of
   daily frequency will be created". The parameter defaults to
   `Frequency.DAILY`, so leaving it out does give daily — but passing `None`
   explicitly, which is exactly what the sentence invites, reaches the
   frequency-to-class table with `None` as the key and raises `KeyError: None`.
   *(observed)* both.

4. **The `to_ymd` position table is wrong for yearly periods.** The docstring
   describes `"middle"` as "the 15th day of the middle month within the original
   period". That holds for half-yearly, quarterly and monthly, whose tables give
   Mar 15 / Sep 15, the 15th of the middle month, and the 15th. `YearlyPeriod`
   maps `"middle"` to June 30. *(observed)* The same description is repeated in
   `to_python_date` and pointed at from `to_iso_string` and `refrequent`.

5. **The SDMX and compact tables both list a weekly row that cannot be
   produced.** `Frequency.WEEKLY` exists, has an entry in `SDMX_REXP_FORMATS`,
   and appears in both string-format tables as `yyyy-Www` and `yyWww` — but
   `PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION` has no weekly class, so every route
   to a weekly period raises `KeyError: <Frequency.WEEKLY: 52>`. *(observed)*
   through `Period.from_ymd` and `Period.from_sdmx_string`.

6. **The name `irispie` survives in twelve places, and the package is
   `datapie`.** Five are `__name__` assignments (`yy.__name__` is literally
   `'irispie.yy'`, and the same for `hh`, `qq`, `mm`, `ii`), one is `dd`'s
   `call_name="irispie.dd"`, and six are the `## ` headings written in this
   pass, which were matched to those `call_name`s so the index links resolve.
   *(observed)* for all six constructors.

   The constructor overview table that used to carry `irispie.yy` through
   `irispie.ii` is gone: it lived in the old `Period.__init__` docstring, which
   this pass replaced with the "Time period constructors" block, and that block
   shows the calls unqualified. So the name no longer appears in any prose —
   only in the six headings and the seven code sites they mirror. This and item
   11 are one finding, and fixing it means changing all thirteen together.

7. `Span.refrequent` shows its call as `new = self.refrequent()` with the
   `new_freq` argument missing, and documents no arguments at all.

8. **The file now carries two documentation layouts.** The entries rewritten in
   this pass use the current form — a `## name` heading, `**Input arguments.**`,
   `### Returns`, `### Examples`. The entries left alone, because their text was
   already accurate, keep the older one: `### Input arguments ###` and `###
   Returns ###` with closing hashes, returns wrapped in `???+ returns "name"`
   markers, and no `## name` heading.

   Twelve of them are decorated and so reach the rendered page:
   `Period.from_sdmx_string`, `Period.today`, `Period.to_python_date`,
   `Period.get_distance_from_origin`, and on `Span`: `copy`, `reverse`, `shift`,
   `shift_end`, `shift_start`, `to_iso_strings`, `to_sdmx_strings` and
   `__add__`. **Eight of these twelve were edited after all**, along with
   `Period.__sub__`, to remove a documented `self` argument; see item 12. Their
   prose is otherwise untouched. Five more decorated entries are one-line
   property taglines rather than full blocks — `Span.start`, `end`, `step`,
   `direction` and `frequency` — which makes seventeen decorated entries left in
   the older form. `Period`'s own `__add__` and its six comparison stubs were
   also left alone but carry no decorator, so they never render. All of them
   still need a structural pass.

9. `Period.__sub__` closes its docstring with a `"""` indented four spaces
   instead of eight. Still a valid docstring; only the reader notices.
10. **Every `@_dm.reference` in this file lacked `add_heading=False`.**
    documark's `reference` decorator prepends its own `☐ \`call_name\`` heading
    unless that flag is set, and the flag defaults to `False` only for classes.
    The original docstrings carried no `##` heading of their own, so the
    auto-heading was the only one and nothing looked wrong.

    Writing the new blocks, which do carry a `## \`name\`` heading, made every
    rewritten entry render two headings. *(observed)* on
    `Period.to_compact_string`, whose docstring held both `☐
    \`to_compact_string\`` and `## \`to_compact_string\``. The flag has now been
    added wherever it was needed. `chartpacks/main.py` (5 of 6) and
    `databoxes/_imports.py` (2 of 2) already did this; this file was the
    outlier.

    The count, so it can be checked against the file: `periods.py` makes **45**
    own `_dm.reference` calls. Of those, **26** now carry a new block with an
    authored `##` heading and all 26 carry `add_heading=False` — these 26 are
    exactly the 21 decorator lines and 5 run-time constructor calls the header
    counts, with `dd`'s decorator among the 21 and `yy`, `hh`, `qq`, `mm`, `ii`
    the five run-time ones; **17** keep their original docstring and documark's
    auto-heading, untouched (see item 8); and **2** are the classes `Period` and
    `Span`, which use a page title with an `===` underline and get no heading of
    either kind — `add_heading` already defaults to `False` for classes, so 26 +
    17 + 2 accounts for all 45. *(observed)*: a census of the module finds no
    docstring carrying both kinds of heading.
11. **The six short constructors constrain what their headings may say.**
    documark builds index anchors from `call_name`, lowercasing it and dropping
    the dots (`_get_anchor`), and the anchor a markdown heading generates comes
    from the heading text. The two have to agree or the index link is dead.

    `yy`, `hh`, `qq`, `mm` and `ii` each have `__name__` assigned literally as
    `"irispie.yy"` and so on, and `dd` is decorated `call_name="irispie.dd"`, so
    the index points at `#irispieyy` and its five siblings. A heading naming
    just `yy` would have given `#yy`, and a dead link. *(observed)* for all six
    before the headings were matched.

    The headings written in this pass therefore spell out the `call_name`, and
    the links resolve today — at the cost of carrying the old package name into
    six new headings. Fixing that properly means changing `__name__`,
    `call_name` and the six headings in one commit; see "Docs vs code" 6.

12. **`self` is no longer listed as an input argument.** It was documented as
    `???+ input "self"` in nine docstrings, all of them in the older form this
    pass otherwise left alone: `Period.to_python_date`, `Period.__sub__`, and on
    `Span` `reverse`, `shift_end`, `shift_start`, `to_iso_strings`,
    `to_sdmx_strings`, `__add__` and `shift`. Eight of the nine are among the
    twelve named in item 8; `Period.__sub__` is the ninth and carries no
    decorator.

    A bound method never receives `self` from its caller, so listing it among
    the arguments a caller supplies is misleading; the same goes for the `klass`
    of a classmethod, which is this file's spelling of `cls`. Nothing written in
    this documentation pass listed either, and the nine older entries have now
    been brought in line. There were no `klass` entries to remove. *(observed)*:
    the file holds none of either.

    Two of the nine — `Span.reverse` and `Span.to_sdmx_strings` — had `self` as
    their only input, so their `### Input arguments ###` heading was dropped
    along with it rather than being left over an empty section.

    **This moves those nine docstrings out of the "left alone" column.** Their
    prose is unchanged and no word was added to any of them — checked token by
    token against the pre-pass file — but they are no longer byte-identical to
    what was there before, and the header and item 8 say so.

    Not done elsewhere: `series/_temporal.py` documents `self` on nine methods
    (`adiff`, `adiff_log`, `aroc`, `apct`, `roc_from_pct`, `pct_from_roc`,
    `pct_from_apct`, `roc_from_apct`, `roc_from_aroc`) and would need the same
    treatment for the package to be consistent.

    Three other entries document `self` and should **keep** it, all three
    checked by parsing the files rather than assumed.
    `broadcast_variants_when_needed` in `series/_broadcasts.py` and
    `disaggregate_arip` in `series/arip.py` are module-level functions whose
    first positional argument really is the series. `hpf` is subtler: it exists
    twice, as a module-level function in `series/_hp.py` and as a `Mixin`
    method-stub, and both document `self` — but the stub's block documents the
    functional form `hpf(self, span=..., ...)`, where the series is passed, so
    its entry describes a real argument too.

### Notes

1. **Nothing is range-checked on construction.** A segment past the end of the
   year rolls forward without a word: `qq(2020, 9)` gives `qq(2022,1)` and
   `mm(2020, 13)` gives `mm(2021,1)`. *(observed)* The docstrings describe
   quarters as "1 to 4" and months as "1 to 12", which is the intent but not a
   rule the code enforces.
2. **Equality across frequencies raises rather than answering.** All six
   comparison operators call `_check_periods` first, `==` and `!=` included, so
   `qq(2020,1) == mm(2020,1)` raises `wrongdoings.Error` instead of returning
   `False`. *(observed)* `__hash__` does not follow suit — it mixes the
   frequency in, so the two hash apart and can share a set without ever being
   compared. *(observed)*
3. `Period ** k` is annotated `-> Span` but returns `self` for `k` of 1 or -1,
   and an `EmptySpan` for 0. *(observed)* The `raise ValueError("Invalid span
   len_dir")` at the end is unreachable: every integer has already matched one
   of the four branches.
4. `IntegerPeriod` inherits the `year` and `segment` properties from `Period`,
   whose bodies are a bare `...`, so both return `None` rather than raising.
   *(observed)*
5. Three members of `Period` exist only to carry documentation.
   `time_period_arithmetics` has an empty body and returns `None`;
   `time_period_comparison` raises `NotImplementedError`; and `_frequency` is a
   property whose getter is declared without a `self` parameter, so reaching it
   raises `TypeError: Period._frequency() takes 0 positional arguments but 1 was
   given`. *(observed)* all three. Same pattern as the documentation stubs in
   `chartpacks/main.py` and `series/_hp.py`.
6. **The lag/lead helpers add where a reader expects subtraction.**
   `long_span_from_short_span` builds `short[0]+max_lag` to
   `short[-1]+max_lead`, so widening a span backwards needs a *negative*
   `max_lag`. Passing `max_lag=1` moves the opening end forward instead,
   producing a long span that does not contain the short one. *(observed)*
   `spans_from_long_span` subtracts both, so the pair are inverses of each
   other; it is annotated `-> Span` while returning a two-tuple of period
   tuples.
7. `periods_from_until` given its endpoints the wrong way round returns an empty
   tuple rather than raising. *(observed)*
8. `periods_from_sdmx_strings` settles the frequency once, from the **first**
   string, and applies it to all of them; a mixed-frequency sequence is not
   detected. *(observed)* — `["2020-Q1", "2020-05"]` raises `ValueError` from
   the quarterly parser. Its `frequency` argument is positional, while the same
   argument on `periods_from_iso_strings` and `periods_from_python_dates` is
   keyword-only.
9. An unresolved span reports neither its state nor a length: `__len__` and
   `__iter__` both return `None`, so `len(span)` raises `TypeError: 'NoneType'
   object cannot be interpreted as an integer` and `list(span)` raises
   `TypeError: iter() returned non-iterator of type 'NoneType'`. *(observed)*
   `bool(span)` is the check that works.
10. `UnknownPeriod` is registered in the frequency-to-class table but is not a
    `Period` subclass and holds one method, `from_sdmx_string`, which returns
    `None` for any input. *(observed)* So reading a period at the unknown
    frequency yields `None` rather than an error.
11. `_period_constructor_with_ellipsis` wraps its whole body in `try: ... except
    ValueError`, meaning to catch only the `args.index(Ellipsis)` that says
    there is no ellipsis. It also catches a `ValueError` raised by the
    constructor on the ellipsis path and retries with the full argument list,
    ellipsis included, so a bad argument is reported as `TypeError:
    RegularPeriodMixin.from_year_segment() takes from 2 to 3 positional
    arguments but 6 were given` rather than as the value error it was.
    *(observed)* on `qq(2020,"x",...,2021,4)`.
12. `Period + k` puts `k` through `int()`, so a float is truncated rather than
    refused: `qq(2020,1) + 1.9` gives `qq(2020,2)`. *(observed)*
13. `Period.from_ymd` forwards to each class's own `from_ymd`, which keeps only
    what its frequency can hold, so the day is silently dropped below daily
    frequency: `Period.from_ymd(Frequency.QUARTERLY, 2020, 5, 17)` gives
    `qq(2020,2)`. *(observed)*
14. `resolve_period_or_integer` tests its argument for being a `Real`, not for
    failing to be a `Period`, so anything that is neither passes through
    unchanged rather than being converted or rejected.
15. `_get_period` swallows everything with a bare `except:` and returns `None`.
16. `EmptySpan` is a singleton — `__new__` caches the first instance — and is
    not a `Span`; it shares only `__iter__`, `__len__` and `shift` with one.
    *(observed)* that two calls give the same object.
17. `dd` is the one short constructor that does not accept `...` to build a
    span; the other five are wrapped and do. *(observed)*
18. `Period.copy` exists although every operation on a period returns a new
    object and nothing mutates one in place.
19. `to_plotly_date`, `to_plotly_edge_before` and `to_plotly_edge_after` carry
    no decorator and empty docstrings, and exist for the plotting layer.
    `IntegerPeriod` overrides all three to return bare numbers rather than
    dates.
20. **The restep operators guard a strict sign, and their messages overstate
    it.** `Span.__rshift__` raises `ValueError("Step must be positive when using
    the >> operator.")` on `step < 0`, and `Span.__lshift__` raises "must be
    negative" on `step > 0`. Zero is neither, so it passes both guards despite
    what the messages say, and the span it produces fails later and elsewhere
    with `ValueError: range() arg 3 must not be zero` the first time its length
    or contents are asked for. *(observed)* through both operators.
21. **`to_compact_string` splits on argument *kind*, not on frequency.**
    `DailyPeriod` declares it `(self, **kwargs)` and swallows any keyword
    silently; the other five declare `(self)` and reject both kinds.
    `IntegerPeriod` shares the method with `to_sdmx_string`. So through
    `Span.to_compact_strings`, a keyword argument works on a daily span and
    raises `TypeError` on every other frequency, while a **positional** argument
    raises on all of them, daily included -- `**kwargs` does not absorb a
    positional. *(observed)* across all six frequencies and both spans. Every
    caller inside the package passes nothing, which is the only form that works
    everywhere.
22. **Twenty-nine of the new `##` headings never render anywhere.** Fifty-five
    blocks in this pass carry a `##` heading; only the 26 on
    `_dm.reference`-decorated entities reach the built page. The other 29 sit on
    undecorated ones — `ResolutionContext`, `IntegerPeriod`, `DailyPeriod`,
    `RegularPeriodMixin`, `UnknownPeriod`, `EmptySpan`, `ContextualPeriod`,
    `Period.copy`, `Period.start`, `Period.end`, `Span.encompassing`,
    `Span.__rshift__`, `Span.__lshift__`, and all sixteen module-level helpers.
    documark never collects them, so the heading shows only through `help()` or
    a source read. Harmless, and consistent with how the rest are written, but
    worth knowing before anyone goes looking for these entries on the reference
    page: they are not there, and adding a heading will not put them there.
23. `Span.encompassing` is a thin classmethod over `get_encompassing_span`,
    returning element 0 of its three-tuple. It is one of the undecorated entries
    listed in note 22.

---

## `frequencies.py`

**Status:** applied. All 8 documented examples run green as doctests, and no
entry carries a doubled heading.

One public class, `Frequency`, an `IntEnum` whose members are the number of
periods of that kind in a year, plus two members outside that reading —
`INTEGER` for numbered observations and `UNKNOWN`. Around it sit a table of SDMX
regular expressions, one predicate over that table, and six module-level
re-exports of the members.

### Bugs

1. **An integer period cannot be read back from the SDMX string it prints.** The
   `INTEGER` entry of `SDMX_PATTERNS` is

       Frequency.INTEGER: _re.compile(r"\([\-\+]?\d+\),", ),

   — the pattern ends in a **comma**. `IntegerPeriod.to_sdmx_string()` produces
   `(1)`, with no comma, so the two do not meet: `ii(1).to_sdmx_string()` gives
   `'(1)'`, and `Frequency.from_sdmx_string("(1)")` then raises
   `wrongdoings.Error: Cannot determine time frequency from "(1)"; probably not
   a valid SDMX string.` *(observed)* `Period.from_sdmx_string("(1)")` fails the
   same way, since it asks this function for the frequency first, and
   `is_sdmx_string("(1)")` is `False`. *(observed)* Appending a comma makes all
   three work. *(observed)*

   The same trailing comma appears in `periods.SDMX_REXP_FORMATS`, so the two
   tables agree with each other and disagree with what the code writes. Every
   other frequency round-trips.

### Docs vs code

1. **Two of the eight members are not exported.** `__all__` carries `YEARLY`,
   `HALFYEARLY`, `QUARTERLY`, `MONTHLY`, `WEEKLY` and `DAILY`, and not `INTEGER`
   or `UNKNOWN`. *(observed)*: `dp.YEARLY` resolves and `dp.INTEGER` does not
   exist, so the two have to be written `Frequency.INTEGER` and
   `Frequency.UNKNOWN`. This is a fact about the code, and it stands.

   The old class docstring made it worse by listing all eight in one table as
   `irispie.YEARLY` through `irispie.UNKNOWN`, implying the last two were
   reachable the same way as the first six. That table was replaced in this
   pass; the block that took its place names the members plainly and says which
   six are exported.
2. **The name `irispie` no longer appears in this file.** It was in all eight
   rows of the old class docstring table and nowhere else here, and that
   docstring has been replaced. *(observed)*: a search of the file finds no
   occurrence.

   Unlike `periods.py` "Docs vs code" 6, nothing constrained the choice — those
   were prose in a table, not headings, so no index anchor depended on them, and
   the replacement uses the bare member names. `periods.py` still carries the
   name in twelve places.
3. **The seven member docstrings all say "Create a ... frequency
   representation".** Nothing is created: `Frequency.YEARLY` is a lookup of an
   existing member, not a constructor. The wording reads as though there were a
   `yearly()` call behind it.

   **Still open.** This pass drafted a block describing the family, not seven
   replacement texts, so the seven were left exactly as they were. Fixing them
   means writing seven short docstrings, which has not been done.
4. `from_letter` and `from_sdmx_string` carry a one-line tagline and nothing
   else — no arguments, no return, and no mention of what either raises, which
   for `from_letter` is the more useful half. `to_jsonable`, `from_jsonable` and
   `is_sdmx_string` have empty docstrings.
5. **Four of the five `@_dm.reference` decorators will need
   `add_heading=False`.** The file has five, and none carries the flag. Four of
   them — `from_letter`, `from_sdmx_string`, `letter` and `is_regular` — sit on
   functions, where documark's auto-heading is on by default, and the blocks
   drafted for them each open with a `## name` heading; applying those four
   without the flag would give each entry two headings. The fifth is on the
   class `Frequency`, where `add_heading` already defaults to `False`, and the
   block drafted for it is a page title with an `===` underline rather than a
   `##` heading, so it needs nothing. Same mechanism as `periods.py` "Docs vs
   code" 10.

   **Done.** The flag is now on those four, and a census of the module finds no
   docstring carrying both kinds of heading. The class decorator was left
   without it, since it needs none.

### Notes

1. **`ANNUAL` and `HALFANNUAL` cannot be found by `from_letter`.** They are
   aliases of `YEARLY` and `HALFYEARLY` — the same objects, confirmed by `is` —
   and enum iteration skips aliases, so the search behind `from_letter` never
   sees a name beginning with `A`. `from_letter("A")` raises a bare
   `StopIteration` carrying no message. *(observed)* So does any other unmatched
   letter; `from_letter("")` raises `IndexError` before the search starts.
   *(observed)*
2. **`from_letter` reads one letter, after dropping underscores.** So
   `"__quarterly__"` gives `QUARTERLY` and `"__description__"` gives `DAILY`.
   *(observed)* both. This is the mechanism behind `databoxes/_imports.py` bug
   5, where the block mark and the description-row heading of a CSV file turn
   out to be indistinguishable to the scanner.
3. **Months and weeks are not range-checked by their patterns.** `2020-00`,
   `2020-13` and `2020-99` all classify as `MONTHLY`, and `2020-W00` and
   `2020-W59` as `WEEKLY`. *(observed)* Half-years and quarters are bounded,
   `[12]` and `[1234]`. So `from_sdmx_string` answers what shape a string has,
   not whether it names a period that exists.
4. **The order of `SDMX_PATTERNS` carries no meaning.** Both callers match with
   `fullmatch`, so a pattern has to cover the whole string; under that rule the
   seven are disjoint and at most one can ever match. `\d\d\d\d` cannot take the
   front of `2020-Q1`, and `MONTHLY` cannot take `2020-01-01`, whichever order
   they sit in.

   *(observed)* two ways: no string out of 200,014 — the realistic ones plus
   200,000 random strings over the alphabet these patterns use — fullmatched
   more than one pattern; and running the classification under all 5,040
   orderings of the dictionary changed no result.

   Worth stating because the opposite is the natural assumption. With `match` or
   `search` instead of `fullmatch`, `\d\d\d\d` **would** eat the front of
   `2020-Q1` and the order would carry the whole correctness argument.
5. **`Frequency.UNKNOWN.__doc__` is the class docstring.** Seven members were
   given a docstring of their own after the class body; `UNKNOWN` was not, so it
   inherits the whole "Time frequencies" page — the same object, not a copy.
   *(observed)*: `Frequency.UNKNOWN.__doc__ is Frequency.__doc__`.

   No character count is given on purpose. An earlier draft of this note
   measured one, and this pass then replaced the class docstring, leaving the
   figure describing text that no longer existed. Any number here rots on the
   next edit to the class docstring, and the identity is the durable fact.
6. **Three of the new `##` headings never render.** `to_jsonable`,
   `from_jsonable` and `is_sdmx_string` carry no `@_dm.reference`, so documark
   never collects them and their headings show only through `help()` or a source
   read. The five decorated entries do render. Same phenomenon as `periods.py`
   note 22, recorded here so that anyone hunting `is_sdmx_string` on the
   reference page knows why it is not there — and that adding a heading will not
   put it there.
7. `SDMX_PATTERNS` is public by name but absent from `__all__`, so it is reached
   as `frequencies.SDMX_PATTERNS`. `UNKNOWN` has no entry in it.
8. `__str__` is overridden to return the member name, and `format` follows it,
   so `f"{Frequency.QUARTERLY}"` gives `QUARTERLY` rather than the `4` an
   `IntEnum` would normally print. *(observed)* `int(freq)` still gives `4`.
9. `to_jsonable` and `from_jsonable` round-trip all eight members, `UNKNOWN`
   included, through the single-letter codes. *(observed)*
10. `WEEKLY` is a full member here, with a value, a letter and an SDMX pattern,
   but `periods.py` has no weekly period class, so every route from a weekly
   frequency to a period raises `KeyError`. See `periods.py` "Docs vs code" 5.
11. `__str__` carries no decorator and no docstring, so it is the one method of
    the class not covered by this pass.
