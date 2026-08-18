# Bug Log — `datapie/src/datapie/chartpacks`

Compiled with AI assistance while documenting this folder. I am new to the
codebase and have not tried to judge which findings are intentional design and
which are defects; everything observed is recorded, and a review from someone
who knows the module would be welcome.

Findings are anchored on method and function names, not line numbers. Items
marked *(observed)* were confirmed by running the code; everything else follows
from reading it.

**No source changes were made in this folder.** The documentation was written as
commented draft blocks; no docstring and no line of executable code was altered.
The drafts were written from the code rather than from the existing docstrings,
several of which are wrong — see "Docs vs code" below.

`main.py` is the only module in the folder.

---

## `main.py`

**Status:** drafts written, not yet applied.

The folder holds one public class, `Chartpack`, and two private ones, `_Figure`
and `_Chart`. A chartpack holds figures, a figure holds charts, and a chart
holds one expression that is evaluated against a `Databox` at plot time.

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

### Docs vs code

1. **The constructor docstring's description of `title` is wrong.** It says the
   title is "used as a basis for creating a caption shown at the top of each
   figure". `Chartpack.title` is assigned in `__init__`, copied in `copy`, and
   read in exactly one other place: `_one_liner`, which builds the `__repr__`
   text. It never reaches a figure or a chart. The caption at the top of a
   plotted figure comes from `_Figure.title`, which is the string passed to
   `add_figure`.
2. The constructor docstring lists a `transforms` argument described as "a
   dictionary of functions that will be applied to the input data before
   plotting", and omits `context` entirely. `transforms` is real — it is a chart
   setting, and `_Chart._apply_transform` looks a named transform up in it — but
   the entry does not say that the name must appear in a chart string as
   `expression[name]` for the lookup to happen. `context` is a real constructor
   parameter and appears nowhere in the docs.
3. **The constructor docstring shows a signature that does not match the code,
   and nothing validates the difference.** It lists `title`, `span`, `tiles`,
   `transforms`, `highlight`, `legend`, `show_legend` and `reverse_plot_order`
   as though they were named parameters; the actual signature is `(title="",
   context=None, **kwargs)`, and those names are recognised only because they
   appear in `_FIGURE_SETTINGS` or `_CHART_SETTINGS`.

   This is worse than an out-of-date signature. `__init__` copies out of
   `kwargs` only the keys already present in those two dictionaries and drops
   everything else without a word, so a user following the documented signature
   and mistyping one of the names — `highlights`, `show_legends`, `chart_types`
   — gets no error, no warning, and a chartpack that quietly ignores the
   setting. A real signature would raise `TypeError` on the same typo. The
   documentation is teaching a calling convention that the code declines to
   check.
4. `Chartpack.plot`, `Chartpack.add_figure` and `Chartpack.num_figures` carry a
   one-line tagline and nothing else — no arguments, no return description. The
   `Chartpack` class docstring is the word "Chartpacks" and nothing more.
5. Most methods have an empty docstring: `copy`, `set_span`, `set_highlight`,
   `modify_figure_titles`, both `format_figure_titles`, `__str__`, `__repr__`,
   `__getitem__`, `__iter__`, and every method of `_Figure` and `_Chart`.

### Notes

1. **`add_figure` is annotated `-> None` but returns the new figure.** The
   return value is the only way to add charts, so every caller uses it. The
   annotation is simply wrong. `_Figure.add_chart`, by contrast, really does
   return `None`, so the two are asymmetric in a way a reader has to discover by
   trying.
2. **`_add_strings` is dead.** The module-level helper is not referenced
   anywhere in `src/datapie` — a grep finds only its own definition. It also
   ignores its first parameter, `self`, and its `**kwargs`.
3. **Two methods are documented but not implemented.** Both have a body of
   `pass`, and both exist only so that documark has somewhere to attach an entry
   for something it cannot otherwise reach. Same pattern as `Series.hpf` in
   `series/_hp.py`.

   | Stub | Page entry | What actually implements it | Calling the stub |
   | ---- | ---------- | --------------------------- | ---------------- |
   | `_constructor_doc` | `Chartpack`, category `constructor` | `Chartpack.__init__`, which is undecorated | `TypeError: Chartpack._constructor_doc() takes 0 positional arguments but 1 was given` *(observed)* |
   | `_add_chart_doc` | `add_chart`, category `add` | `_Figure.add_chart`, on a private class `document_namespace` cannot collect | returns `None` *(observed)* |

   The consequence is that every entry on the rendered page under those two
   names describes code that lives somewhere else. A reader who finds
   `Chartpack` in the reference and goes looking for a method of that name finds
   a stub; the same for `add_chart`.

   `_constructor_doc` is declared `@classmethod` but takes no parameters at all,
   not even `cls`, so it cannot be called successfully by any route. That is
   harmless while nothing calls it, and it is the clearest signal that it was
   never meant to run.

   Both carried documentation before this pass, and both were wrong: the
   constructor entry described a signature the code does not have and a `title`
   argument that does nothing (see "Docs vs code" 1 and 3), and the `add_chart`
   entry was a single tagline with no arguments and no return description. The
   rewritten blocks were written from the implementing code — `__init__` and
   `_Figure.add_chart` respectively — rather than from the stubs they sit on.
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

   The other four sites fail that call too, for a different reason: `Self`,
   `Callable` and `Iterable` sit behind the `TYPE_CHECKING` guard and are
   equally absent at runtime, so supplying `Any` alone repairs only
   `Chartpack.plot` and the rest still raise on the guarded names. *(observed)*
   That part is the ordinary cost of the guard rather than a defect; what marks
   `Any` out is that it is missing from the guarded block as well, so a static
   checker reads it as an undefined name while the other five are fine. Same
   finding as `databoxes/_views.py` bug 2 and `databoxes/_exports.py` note 10.
10. **`_Chart.plot` annotates `legend: Iterable[str, ...] | None`.** `Iterable`
    takes one type argument; `[str, ...]` is tuple syntax. The annotation is
    never evaluated in this module, for both of the reasons in note 9: `from
    __future__ import annotations` leaves it the string `'Iterable[str, ...] |
    None'` *(observed)*, and `Iterable` is `TYPE_CHECKING`-only and therefore
    unbound at runtime, so `typing.get_type_hints(_Chart.plot)` raises
    `NameError: name 'Iterable' is not defined` *(observed)* and never reaches
    the question of arity at all.

    What let the typo through is the spelling. Where such an annotation *is*
    evaluated, `collections.abc.Iterable[str, ...]` builds a
    `types.GenericAlias` and does no arity checking, while `typing.Iterable[str,
    ...]` raises `TypeError: Too many arguments for typing.Iterable; actual 2,
    expected 1`. *(observed)* of the two spellings on their own in a plain
    interpreter — not of this file, where neither is reached. So nothing at
    runtime will report this one; only a reader or a static checker will.

    The value that arrives is `_Figure.legend`, which `_Figure.plot` passes to
    `_Chart.plot`, which forwards it to `Series.plot` — annotated there `str |
    Iterable[str] | None`. So `Iterable[str] | None` is what was meant.
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
14. **The `show_legend` derivation in `_Figure.__init__` is dead on every
    reachable path.** The last line of `__init__` is

        if self.show_legend is None:
            self.show_legend = self.legend is not None and bool(self.legend)

    which reads as "show the legend when one was given". It cannot do that.
    `__init__` has just set every slot to `None`, so `self.legend` is `None`
    whenever the line runs and the derivation can only ever produce `False`.
    *(observed)*

    Both routes that actually build a figure then overwrite it. `from_string`
    and `copy` each loop over `_FIGURE_SETTINGS_KEYS`, which contains
    `show_legend`, and `setattr` it from the keyword, the cascade, or the module
    default — and `_FIGURE_SETTINGS["show_legend"]` is `None`. So a figure made
    through `add_figure` carries `show_legend=None` whether or not a `legend`
    was passed: `from_string("F", legend=("a","b"), )` gave `legend=('a', 'b')`
    with `show_legend=None`, and `copy` carried the same pair across.
    *(observed)*

    `_Figure.plot` sets `figure.update_layout(showlegend=self.show_legend, )` in
    its final update_layout, so plotly is handed `None` — no instruction — and
    falls back to its own rule rather than the one the derivation intended.
    *(observed)*: a one-chart figure built with `legend=("series a",)` came back
    with `layout.showlegend` of `None`, the trace itself carrying
    `showlegend=True`. Passing `show_legend=True` to `add_figure` works and is
    the only way to set it. Nothing in the documentation claims otherwise, so
    this is a dead branch rather than a docs-versus-code collision.
