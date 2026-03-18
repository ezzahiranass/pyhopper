"""
Auto-generate one reference page per Python module under pyhopper/Components/
and pyhopper/Core/, plus a SUMMARY.md for literate-nav.

This script is executed by the mkdocs-gen-files plugin on every build.
Adding a new component file automatically adds a new reference page.
"""

from pathlib import Path
import mkdocs_gen_files

PACKAGE_ROOT = Path(__file__).parent.parent / "pyhopper"

# Modules that belong in the Core section (listed explicitly for ordering)
CORE_MODULES = [
    "Core.Atoms",
    "Core.DataTree",
    "Core.Branch",
    "Core.Path",
    "Core.Component",
]

nav = mkdocs_gen_files.Nav()

# ── Core ────────────────────────────────────────────────────────────
for dotted in CORE_MODULES:
    parts = dotted.split(".")
    module_path = PACKAGE_ROOT.joinpath(*parts).with_suffix(".py")
    if not module_path.exists():
        continue

    doc_path = Path("reference", "Core", parts[-1] + ".md")
    nav_doc_path = Path("Core", parts[-1] + ".md")
    full_dotted = "pyhopper." + dotted

    with mkdocs_gen_files.open(doc_path.as_posix(), "w") as f:
        f.write(f"# {parts[-1]}\n\n")
        f.write(f"::: {full_dotted}\n")

    nav["Reference", "Core", parts[-1]] = nav_doc_path.as_posix()

# ── Components (auto-walk) ───────────────────────────────────────────
components_root = PACKAGE_ROOT / "Components"

for src_path in sorted(components_root.rglob("*.py")):
    if src_path.name.startswith("_"):
        continue
    if src_path.stat().st_size == 0:
        continue

    # Build the dotted module name
    rel = src_path.relative_to(PACKAGE_ROOT.parent)     # pyhopper/Components/...
    dotted = ".".join(rel.with_suffix("").parts)         # pyhopper.Components.Transform.Move

    # Build the doc path:  reference/Components/Transform/Move.md
    rel_parts = src_path.relative_to(components_root).with_suffix("").parts
    doc_path  = Path("reference", "Components", *rel_parts).with_suffix(".md")
    nav_doc_path = Path("Components", *rel_parts).with_suffix(".md")

    # Nav breadcrumbs:  Reference > Components > Transform > Move
    nav_parts = ("Reference", "Components") + rel_parts

    with mkdocs_gen_files.open(doc_path.as_posix(), "w") as f:
        title = rel_parts[-1]
        f.write(f"# {title}\n\n")
        f.write(f"::: {dotted}\n")

    nav[nav_parts] = nav_doc_path.as_posix()

# ── Utils/Exporters ─────────────────────────────────────────────────
for src_path in sorted((PACKAGE_ROOT / "Utils").rglob("*.py")):
    if src_path.name.startswith("_"):
        continue

    rel = src_path.relative_to(PACKAGE_ROOT.parent)
    dotted = ".".join(rel.with_suffix("").parts)
    rel_parts = src_path.relative_to(PACKAGE_ROOT / "Utils").with_suffix("").parts
    doc_path  = Path("reference", "Utils", *rel_parts).with_suffix(".md")
    nav_doc_path = Path("Utils", *rel_parts).with_suffix(".md")
    nav_parts = ("Reference", "Utils") + rel_parts

    with mkdocs_gen_files.open(doc_path.as_posix(), "w") as f:
        f.write(f"# {rel_parts[-1]}\n\n")
        f.write(f"::: {dotted}\n")

    nav[nav_parts] = nav_doc_path.as_posix()

# ── Write SUMMARY.md for literate-nav ───────────────────────────────
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
