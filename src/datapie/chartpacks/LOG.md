# Bug Log — `datapie/src/datapie/chartpacks`

Compiled while documenting this folder. Items marked *(observed)* were
confirmed by running the code; the rest follow from reading it. Findings are
anchored on method and function names, not line numbers.

I am new to the codebase and have not judged which findings are intentional
design and which are defects — everything observed is recorded.

`main.py` is the only module in the folder. It holds one public class,
`Chartpack`, and two private ones, `_Figure` and `_Chart`. A chartpack holds
figures, a figure holds charts, and a chart holds one expression that is
evaluated against a `Databox` at plot time.

---

## `main.py`

### Bugs

1. **`format_figure_titles` is defined twice in the `Chartpack` body, and the
   surviving definition is the unsafe one.** The first assigns `f.title =
   f.title.format(**kwargs) if f.title else f.title`, guarding a missing title.
   The second, which shadows it, delegates to `_Figure.format_figure_title`,
   which calls `self.title.format(**kwargs)` with no guard at all.
   `_Figure.__init__` accepts `title=None` and `Chartpack.add_figure` is the
   only documented way to create one, so a figure whose title is `None` raises
   `AttributeError: 'NoneType' object has no attribute 'format'`.

2. **A `transform` inherited from the figure is consumed by the first chart.**
   `_Chart.from_string` resolves the transform with
   `chart_settings_cascaded.pop("transform", None)`. The dictionary it is handed
   is `_Figure._chart_settings` itself, not a copy, so the key is removed
   permanently. The first chart added to a figure inherits the transform; every
   chart added afterwards does not.

   Silent and wrong-output rather than loud: the later charts plot untransformed
   data under captions that do not mention a transform, so nothing on screen
   says anything is missing. Same class of defect as the `update_layout`
   mutation in `series/_plotly.py`.

3. **`Chartpack.copy` drops the context.** It builds the new object through
   `type(self)()`, whose `__init__` sets `self._context = context` with
   `context` defaulting to `None`, and then assigns `title`, `figures`,
   `_figure_settings`, `_chart_settings` and `_description` — but never
   `_context`. A copy therefore evaluates its chart expressions without whatever
   context the original was given, and any name that came from the context fails
   to resolve.

4. **`Chartpack.plot` accepts `**kwargs` and never reads them.** The parameter
   is in the signature; no line of the body touches it. Anything passed there —
   including a misspelled `show_figure` for `show_figures`, or any of the figure
   or chart settings a caller might reasonably expect to override at plot time —
   is discarded without error.

5. **A mistyped setting is accepted and silently dropped.** The signature is
   `(title="", context=None, **kwargs)`, and `__init__` copies out of `kwargs`
   only the keys already present in `_FIGURE_SETTINGS` or `_CHART_SETTINGS`,
   discarding everything else without a word. *(observed)*:
   `Chartpack(title="T", highlights="typo", show_legends=True,
   chart_types="x")` was built without error and none of the three settings
   took effect, while the correctly spelled `highlight="ok"` reached
   `_figure_settings`. A real named parameter would raise `TypeError` on the
   same typo.

### Security

1. **A chart string carries arbitrary Python, executed at plot time.**
   `_Chart._apply_transform` compiles the transform portion of a chart string
   with `eval("lambda x:" + self.transform)` and then calls the result on the
   series. Building the lambda is inert; calling it is not, so anything written
   between the brackets of `"expression[...]"` runs with the privileges of the
   process the moment `plot` is reached.

   This is recorded on its own rather than among the Notes because it is a
   property of the design, not a curiosity. Chartpacks are exactly the kind of
   object that gets passed between colleagues, checked into a repository, or
   generated from a configuration file, and a chart string reads like data — a
   short label with an expression in it — rather than like code. Nothing in the
   type of the argument, in the docstrings, or at the call site suggests
   otherwise.

   Unremarkable while every pack is written by the person running it. Worth a
   decision before a pack is ever built from input the author did not write.

### Notes

1. **`add_figure` is annotated `-> None` but returns the new figure.** The
   return value is the only way to add charts, so every caller uses it. The
   annotation is simply wrong. `_Figure.add_chart`, by contrast, really does
   return `None`, so the two are asymmetric in a way a reader has to discover by
   trying.
2. **`_add_strings` is dead.** The module-level helper is not referenced
   anywhere in `src/datapie` — a grep finds only its own definition. It also
   ignores its first parameter, `self`, and its `**kwargs`.
3. **Two methods have a body of `pass` and cannot be used.**
   `_constructor_doc` is declared `@classmethod` but takes no parameters at
   all, not even `cls`, so calling it raises `TypeError:
   Chartpack._constructor_doc() takes 0 positional arguments but 1 was given`.
   *(observed)* `_add_chart_doc` returns `None`. *(observed)* The work is done
   by `Chartpack.__init__` and `_Figure.add_chart` respectively.

4. `Chartpack.__getitem__` accepts an integer or a string. A string is matched
   against figure titles with `next(...)` and no default, so a title matching
   nothing raises `StopIteration` rather than `KeyError`. Any other type falls
   through both branches and returns `None`.
5. `_resolve_tiles` reads a bare integer as a chart count, not a row count.
6. `_Figure.add_charts` iterates its argument directly, so a bare string is
   consumed character by character and produces one chart per character. Only
   `Chartpack.add_figure` has the string/iterable guard, in the unused
   `_add_strings`.
7. `Chartpack.set_span` reaches through to the charts, while
   `Chartpack.set_highlight` assigns to the figures. Both are consistent with
   where the setting lives — `span` is a chart setting, `highlight` a figure
   setting — but neither affects figures or charts added afterwards.
8. `Chartpack` is not referenced anywhere else in `src/datapie`. It is reachable
   only as `dp.Chartpack`.
9. **`Any` is used in five annotations and never imported.** `Chartpack.plot`
   (`-> dict[str, Any] | None`), both `*_cascaded` parameters of
   `_Figure.from_string`, `chart_settings_cascaded` in `_Chart.__init__`, and
   the same parameter of `_Chart.from_string`. The `TYPE_CHECKING` block imports
   `Self`, `Callable`, `Iterator`, `Iterable` and `EllipsisType`, and not `Any`.
   Nothing fails at runtime, since `from __future__ import annotations` keeps
   every annotation a string, but `typing.get_type_hints(Chartpack.plot)` raises
   `NameError: name 'Any' is not defined`. *(observed)*

   What marks `Any` out from the other guarded names is that it is missing from
   the `TYPE_CHECKING` block as well, so a static checker reads it as an
   undefined name. Same finding as `databoxes/_views.py` bug 2 and
   `databoxes/_exports.py` note 10.
10. **`_Chart.plot` annotates `legend: Iterable[str, ...] | None`.**
    `Iterable` takes one type argument; `[str, ...]` is tuple syntax. Nothing
    reports it — `from __future__ import annotations` leaves the annotation a
    string, and `Iterable` is `TYPE_CHECKING`-only, so
    `typing.get_type_hints(_Chart.plot)` raises `NameError: name 'Iterable' is
    not defined` before arity is ever considered. *(observed)* Only a reader or
    a static checker will catch it.

    The value that arrives is `_Figure.legend`, which `_Figure.plot` passes to
    `_Chart.plot`, which forwards it to `Series.plot` — annotated there
    `str | Iterable[str] | None`. So `Iterable[str] | None` is what was meant.

11. **`import copy as _cp` is dead.** `_cp` appears nowhere else in the file.
    All three `copy` methods build their result by hand instead —
    `Chartpack.copy` and `_Figure.copy` through `type(self)()` followed by
    attribute assignment and dictionary comprehensions, `_Chart.copy` by passing
    the four core attributes to the constructor and looping over the chart
    settings.
12. **Two locals in `_tree_repr` are computed and never read.** `child_repr_func
    = _ft.partial(_tree_repr, indent=child_indent, )` is never called — the
    comprehension under it calls `_tree_repr` directly — and `num_child_objects
    = len(child_objects)` is never read, the same `len(child_objects)` being
    recomputed inside that comprehension. Dropping both leaves the rendered tree
    identical. *(observed)* `child_repr_func` is also the only use of `_ft`, so
    removing it makes `import functools as _ft` dead in turn, leaving `_re` as
    the only one of the three standard-library imports that is used at all.
13. **The guard in `num_figures` does nothing.** The body is `return
    len(self.figures, ) if self.figures else 0`, and `len([])` is already `0`.
    `figures` is assigned a list in `__init__` and in `copy` and is never set to
    `None`, so no reachable state tells the two branches apart; an empty pack
    reports `0` either way. *(observed)*
14. **The `show_legend` derivation in `_Figure.__init__` is dead.** The last
    line of `__init__` is

        if self.show_legend is None:
            self.show_legend = self.legend is not None and bool(self.legend)

    which reads as "show the legend when one was given". It cannot do that:
    `__init__` has just set every slot to `None`, so `self.legend` is always
    `None` when the line runs and the derivation can only produce `False`.
    *(observed)*

    Both routes that build a figure then overwrite it — `from_string` and
    `copy` each `setattr` `show_legend` from the keyword, the cascade, or the
    module default, which is `None`. So a figure made through `add_figure`
    carries `show_legend=None` whether or not a `legend` was passed.
    *(observed)* `_Figure.plot` then hands plotly `showlegend=None`, no
    instruction, and it falls back to its own rule. Passing `show_legend=True`
    to `add_figure` works and is the only way to set it. *(observed)*
