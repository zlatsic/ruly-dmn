# Ruly-DMN

`ruly-dmn` is a python package that offers a limited implementation of the DMN
standard, with additional features. It relies on the
[`ruly`](https://ruly.readthedocs.io/en/latest/) rule engine to make decisions
and derive new rules. It can be used as a library or as a command line tool.

The package assumes that the DMN diagrams are defined as XML files, in the
format specified by the [Camunda
modeler](https://camunda.com/download/modeler/). The recommended workflow is to
use the Camunda modeler to create diagrams and initial decision tables and then
pass them to functions in this package, so it can make decisions or derive new
rules. See the `examples` directory for examples of working DMN files that can
both be opened in the Camunda modeler and passed to the functions of this
package.

The current limitations, in regard to the complete DMN standard:

  * only available hit policy is FIRST
  * there are no constraints on enumerated variables when user is entering new
    rules
  * only available variable comparision (when making decisions) is for equality
  * visual diagrams are not taken into account when creating rule engine rules,
    only decision tables
  * the package functions are not guarenteed to work if the DMN file is
    incorrect
  * S-Feel and other code evaluations in rules are not supported


## Installation

To install, call:

```bash
pip install ruly-dmn
```

## Usage

When the package is installed, it can be used either by importing its modules
(see documentation for more details), or by calling `ruly-dmn` in command line.
Alternatively, `python -m ruly_dmn.main` may be used instead of the command
line tool. Also it's possible to use this tool as a library, consult the
documentation for that.

## Development environment

To install development dependencies, call

```bash
pip install -r requirements.txt
```

This will, among other packages, install `doit`, which is `ruly-dmn`'s build
tool. Use this tool to perform various actions like testing, building
documentation, linting check, etc. For the list of all available tasks, call:

```bash
doit list
```

## Contributing

Feel free to post any issues - bugs, feature requests, etc. Do not send pull
requests before an issue for the problem it solves is created. When sending
pull requests, please reference the issue(s) it attempts to solve and, after
the review process, it will be accepted. Make sure that the updated changes
reflect on the documentation and tests, so they're not left in an inconsistent
state.
