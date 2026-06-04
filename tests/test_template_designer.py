from pathlib import Path
import ast
import sys
import json


ROOT = Path(__file__).resolve().parents[1]
BASE_VIEW = ROOT / "views" / "base.jinja2"
DESIGNER_VIEW = ROOT / "views" / "templatedesigner.jinja2"
APP_FILE = ROOT / "brother_ql_web.py"


def test_base_view_exposes_template_designer_navigation():
    content = BASE_VIEW.read_text(encoding="utf-8")

    assert '<a href="/templatedesigner">Template Designer</a>' in content


def test_template_designer_view_loads_rjsf_dependencies():
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert '@rjsf/core@4.2.2/dist/react-jsonschema-form.js' in content
    assert 'id="designerFormMount"' in content


def test_backend_exposes_template_designer_schema_api_and_page_route():
    content = APP_FILE.read_text(encoding="utf-8")

    assert '@route("/templatedesigner")' in content
    assert "@route('/api/template/designer/schema'" in content
    assert 'def build_template_designer_schema():' in content


def test_builtin_elements_define_get_definition():
    elements_dir = ROOT / "elements"
    missing = []

    for file_path in elements_dir.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue

            bases = [ast.unparse(base) for base in node.bases]
            if not any("ElementBase" in base for base in bases):
                continue

            has_get_definition = any(
                isinstance(member, ast.FunctionDef) and member.name == "get_definition"
                for member in node.body
            )
            if not has_get_definition:
                missing.append(f"{file_path.name}:{node.name}")

    assert missing == [], f"Missing get_definition in element classes: {missing}"


def test_schema_has_no_phantom_definition_refs():
    """No $ref in the generated schema should point to a missing definition."""
    # Ensure the elements package can be imported from the project root.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from elements import ElementBase
    from brother_ql_web import build_template_designer_schema

    payload = build_template_designer_schema()
    schema = payload["schema"]
    definitions = schema.get("definitions", {})
    known_keys = set(definitions.keys())

    def find_phantom_refs(node, path=""):
        phantom = []
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if ref.startswith("#/definitions/"):
                    ref_key = ref[len("#/definitions/"):]
                    if ref_key not in known_keys:
                        phantom.append(f"{path} -> {ref}")
            for k, v in node.items():
                phantom.extend(find_phantom_refs(v, f"{path}.{k}"))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                phantom.extend(find_phantom_refs(item, f"{path}[{i}]"))
        return phantom

    phantom = find_phantom_refs(schema)
    assert phantom == [], f"Schema contains $refs to missing definitions: {phantom}"
