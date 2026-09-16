# Bug Log — `datapie/src/datapie` (package root)

Compiled while documenting `periods.py` and `frequencies.py`. Items marked
*(observed)* were confirmed by running the code; the rest follow from reading
it. Findings are anchored on method and function names, not line numbers.

I am new to the codebase and have not judged which findings are intentional
design and which are defects — everything observed is recorded.

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

8. **`from_iso_string` and `from_python_date` raise on an explicit
   `frequency=None`.** The parameter defaults to `Frequency.DAILY`, so leaving
   it out gives daily — but passing `None` reaches the frequency-to-class table
   with `None` as the key and raises `KeyError: None`. *(observed)* both.
9. **`Span.__sub__` against a period stops one short.** It builds
   `range(self._start-offset, self._end-offset, self._step)`, while the
   `_serials` property that drives iteration builds the same range with
   `+_sign(step)` added to the stop. For a four-period span, `span - span.start`
   gives `range(0, 3)` — three values against four periods. *(observed)* The two
   are meant to line up and do not.

### Docs vs code

1. **The `to_ymd` position table is wrong for yearly periods.** The docstring
   describes `"middle"` as "the 15th day of the middle month within the original
   period". That holds for half-yearly, quarterly and monthly, whose tables give
   Mar 15 / Sep 15, the 15th of the middle month, and the 15th. `YearlyPeriod`
   maps `"middle"` to June 30. *(observed)* The same description was repeated in
   `to_python_date`, whose block has since been rewritten and now carries a
   per-frequency table with June 30 in it. `to_ymd` itself still has the wrong
   wording, and `to_iso_string` and `refrequent` still point at it.

2. **The SDMX and compact tables both list a weekly row that cannot be
   produced.** `Frequency.WEEKLY` exists, has an entry in `SDMX_REXP_FORMATS`,
   and appears in both string-format tables as `yyyy-Www` and `yyWww` — but
   `PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION` has no weekly class, so every route
   to a weekly period raises `KeyError: <Frequency.WEEKLY: 52>`. *(observed)*
   through `Period.from_ymd` and `Period.from_sdmx_string`.

3. **`Period.from_sdmx_string` trusts a frequency it is given and never
   checks it against the string.** The old block described `frequency` only as
   an efficiency: "if `None`, the frequency is inferred from the SDMX string
   itself; supplying the frequency is more efficient if it is known in
   advance." It is also a way to get a confusing error.
   `Period.from_sdmx_string("2020-Q1", Frequency.MONTHLY)` raises `ValueError:
   invalid literal for int() with base 10: 'Q1'` from inside the monthly
   parser. *(observed)* Nothing says the frequency and the string disagreed.

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
5. **`Period._frequency` cannot be read.** The property's getter is declared
   without a `self` parameter, so reaching it raises `TypeError:
   Period._frequency() takes 0 positional arguments but 1 was given`.
   *(observed)* Two neighbouring members are stubs: `time_period_arithmetics`
   has an empty body and returns `None`, and `time_period_comparison` raises
   `NotImplementedError`.
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
12. **A non-integer offset is truncated, not refused.** `Period + k` puts `k`
    through `int()`, so `qq(2020,1) + 1.9` gives `qq(2020,2)`, and `Span + k`
    inherits it — `span + 1.5` moves the span one period forward and
    `span + -1.5` one back. *(observed)* all three.
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
18. **The restep operators guard a strict sign, and their messages overstate
    it.** `Span.__rshift__` raises `ValueError("Step must be positive when using
    the >> operator.")` on `step < 0`, and `Span.__lshift__` raises "must be
    negative" on `step > 0`. Zero is neither, so it passes both guards despite
    what the messages say, and the span it produces fails later and elsewhere
    with `ValueError: range() arg 3 must not be zero` the first time its length
    or contents are asked for. *(observed)* through both operators.
19. **`to_compact_string` splits on argument *kind*, not on frequency.**
    `DailyPeriod` declares it `(self, **kwargs)` and swallows any keyword
    silently; the other five declare `(self)` and reject both kinds.
    `IntegerPeriod` shares the method with `to_sdmx_string`. So through
    `Span.to_compact_strings`, a keyword argument works on a daily span and
    raises `TypeError` on every other frequency, while a **positional** argument
    raises on all of them, daily included -- `**kwargs` does not absorb a
    positional. *(observed)* across all six frequencies and both spans. Every
    caller inside the package passes nothing, which is the only form that works
    everywhere.
20. **`Period.today` works only for the calendar frequencies.**
    `Period.today(freq)` looks `freq` up in
    `PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION` and calls `from_ymd` on what it
    finds. `Frequency.INTEGER` resolves to a class with no calendar, and the
    call raises `KeyError` naming the current *year* — `KeyError: 2026` when run
    in 2026 — which points at nothing a caller would recognise. *(observed)*
    `None` raises `KeyError: None`. The integer value of a calendar frequency
    works as well as the member: `Period.today(4)` equals
    `Period.today(Frequency.QUARTERLY)`. *(observed)*
21. **`Span.to_sdmx_strings` forwards arguments to a method that takes none.**
    Its signature is `(self, *args, **kwargs)` and it hands them to
    `to_sdmx_string` on each period, which accepts nothing beyond `self`. So the
    only correct call is the empty one; `to_sdmx_strings(position="end")` raises
    `TypeError: QuarterlyPeriod.to_sdmx_string() got an unexpected keyword
    argument 'position'`. *(observed)* Its sibling `to_iso_strings` has the same
    signature and does forward a useful `position`, which makes the asymmetry
    easy to trip over.

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
   `Frequency.UNKNOWN`.
2. **The seven member docstrings all say "Create a ... frequency
   representation".** Nothing is created: `Frequency.YEARLY` is a lookup of an
   existing member, not a constructor. The wording reads as though there were a
   `yearly()` call behind it.

   **Still open.** This pass drafted a block describing the family, not seven
   replacement texts, so the seven were left exactly as they were. Fixing them
   means writing seven short docstrings, which has not been done.

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
4. `SDMX_PATTERNS` is public by name but absent from `__all__`, so it is reached
   as `frequencies.SDMX_PATTERNS`. `UNKNOWN` has no entry in it.
5. `__str__` is overridden to return the member name, and `format` follows it,
   so `f"{Frequency.QUARTERLY}"` gives `QUARTERLY` rather than the `4` an
   `IntEnum` would normally print. *(observed)* `int(freq)` still gives `4`.
6. `to_jsonable` and `from_jsonable` round-trip all eight members, `UNKNOWN`
   included, through the single-letter codes. *(observed)*
7. `WEEKLY` is a full member here, with a value, a letter and an SDMX pattern,
   but `periods.py` has no weekly period class, so every route from a weekly
   frequency to a period raises `KeyError`. See `periods.py` "Docs vs code" 5.
