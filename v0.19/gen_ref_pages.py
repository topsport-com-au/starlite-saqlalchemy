"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files
from mkdocs_gen_files.nav import Nav

# Ignore is due to `Nav.__init__()` having no typed arguments and no `-> None:` so mypy infers it
# to be untyped.
nav = Nav()  # type:ignore[no-untyped-call]

for path in sorted(Path("src").rglob("*.py")):  #
    module_path = path.relative_to("src").with_suffix("")
    doc_path = path.relative_to("src").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = module_path.parts

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)  # pylint: disable=invalid-name
        fd.write(f"::: {identifier}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
