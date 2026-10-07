# DataPie

Time series and data management for macroeconomic modeling


---


## Project URLs

Homepage:
[`https://github.com/iris-solutions-team/datapie`](https://github.com/iris-solutions-team/datapie)

Documentation:
[`https://iris-solutions-team.github.io/datapie-pages`](https://iris-solutions-team.github.io/datapie-pages)

Tutorials:
[`https://github.com/IRIS-Solutions-Team/datapie-tutorials`](https://github.com/IRIS-Solutions-Team/datapie-tutorials)

Issue tracker:
[`https://github.com/iris-solutions-team/datapie/issues`](https://github.com/iris-solutions-team/datapie/issues)


---


## What is DataPie

DataPie is a Python package for working with dated data, the kind found in
macroeconomic modeling and analysis. It provides the data layer on which
[IrisPie](https://github.com/iris-solutions-team/irispie-ce), a macroeconomic
modeling package, is built, and it can also be used on its own.

The package offers:

- **Periods and frequencies** – date objects for yearly, half-yearly,
  quarterly, monthly, and other regular frequencies, with arithmetic,
  ranges, and conversions between frequencies.

- **Time series** – series indexed by periods, with arithmetic,
  transformations, moving-window functions, filtering (such as the
  Hodrick-Prescott filter), seasonal adjustment based on X13, and tools for
  filling and extrapolating missing observations.

- **Databoxes** – dictionary-like containers that hold time series and other
  objects together, with tools for importing, exporting, merging, and
  running Python scripts that populate them.

- **Charts** – plotting of time series and databoxes based on Plotly,
  including packaged sets of charts that can be produced in one go.


---


## Installation

```bash
pip install datapie
```

DataPie requires Python 3.11 or later.


---


## License

DataPie is released under the [MIT License](LICENSE). Copyright (c) 2025 Iris
Solutions Team.

Note that this differs from IrisPie, which is distributed under separate
source-available licenses; see the IrisPie documentation for details.
