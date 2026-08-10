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

I also swapped Notes and Docs-vs-code — bugs and verified