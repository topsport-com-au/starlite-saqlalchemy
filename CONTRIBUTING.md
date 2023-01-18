# Contributor Documentation

Thanks for taking an interest in `starlite-saqlalchemy`!

Hopefully this document makes it easy for you to get started contributing to `starlite-saqlalchemy`,
if not, [let us know!](https://github.com/topsport-com-au/starlite-saqlalchemy/issues)

## Workflow

### Local Environment for IDE

First install the library and dependencies:

`poetry install`

Then install test dependencies into local env for benefit of IDE:

`poetry run pip install -r dev.requirements.txt`

We use `pre-commit` and `tox` for code quality and testing.

_Suggestion: [pipx](https://pypa.github.io/pipx/) makes installing python tools easy!_

### Install pre-commit

`pipx install pre-commit`

#### install the git hooks

`pre-commit install --hook-type pre-commit --hook-type commit-msg`

This command makes configures a bunch of tools to run before commit and during commit of your
changes. These are mostly for code cleanliness and style, and one is to ensure our commits conform
to [conventional commits](https://www.conventionalcommits.org), which is important for release
automation.

Installing and running these tools locally is recommended so that you don't need to wait for CI to
fail - time is precious!

Pre-commit hooks can be run on demand, the following will run all hooks:

`pre-commit run --all-files`

This runs just `flake8`:

`pre-commit run flake8 --all-files`

#### install tox

`pipx install tox`

Tox is a tool that runs test commands in isolated environments. There are a few different test
environments configured, and these commands are the exact same ones that are run in CI, so no
surprises!

For example:

- `tox -e py310` - run the unittests on python 3.10.<sup>[1](#tox1)</sup>
- `tox -e py311` - run the unittests on python 3.11.<sup>[1](#tox1)</sup>
- `tox -e coverage` - unit test coverage report.
- `tox -e mypy` - runs mypy static type checker on the source.
- `tox -e pyright` - runs pyright static type checker on the source.
- `tox -e integration` - runs the dockerized integration test suite.
- `tox` - run everything, you maniac!

<a name="tox1">1</a>. Must have the Python versions installed.
[pyenv](https://github.com/pyenv/pyenv) is a useful tool for maintaining multiple python versions on
your system.

The first time you run a tox environment it will take a bit longer as it needs to install the
dependencies. After that, the existing environment is reused, so it is nice and fast. If you find
that you need to recreate an tox environment use the `-r` flag, e.g., `tox -e mypy -r`.

## CI

We run pre-commit and all of the above tox environments in CI (except for `refurb`), so if they are
passing locally, you should be all good when your PR is made.

## Conventional Commits

Use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification when
drafting your commit message.

> 1. fix: a commit of the type fix patches a bug in your codebase (this correlates with PATCH in
>    Semantic Versioning).
> 2. feat: a commit of the type feat introduces a new feature to the codebase (this correlates with
>    MINOR in Semantic Versioning).
> 3. BREAKING CHANGE: a commit that has a footer BREAKING CHANGE:, or appends a ! after the
>    type/scope, introduces a breaking API change (correlating with MAJOR in Semantic Versioning). A BREAKING CHANGE can be part of commits of any type.
>    types other than fix: and feat: are allowed, for example @commitlint/config-conventional (based on the the Angular convention) recommends build:, chore:, ci:, docs:, style:, refactor:, perf:, test:, and others.
>    footers other than BREAKING CHANGE: <description> may be provided and follow a convention similar to git trailer format.

See [the docs](https://www.conventionalcommits.org/en/v1.0.0/) for more examples.

Note: If you followed the [pre-commit](#install-pre-commit) instructions above, you already have a
hook installed that will help you to conform to the specification.

## Semantic Releases

We enforce [Conventional Commits](#conventional-commits) as they drive
[Semantic Release](https://python-semantic-release.readthedocs.io/en/latest/#). Releases are made
automatically on push into `main` and the incremented version is determined based on the commit
message.

This means updates made are available as soon as practically possible!
