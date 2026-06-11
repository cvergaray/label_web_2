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

    assert '/static/js/vendor/react.production.min.js' in content
    assert '/static/js/vendor/react-dom.production.min.js' in content
    assert '/static/js/vendor/react-jsonschema-form-4.2.2.js' in content
    assert '/static/js/vendor/js-yaml.min.js' in content
    assert 'id="designerFormMount"' in content
    assert 'id="templateFormat"' in content
    assert '<option value="yaml" selected>YAML</option>' in content
    assert "var outputFormat = 'yaml';" in content
    assert 'id="designerPreviewImg"' in content
    assert 'id="previewPrinter"' in content
    assert 'id="previewLabelSize"' in content
    assert 'id="designerLayoutWide"' in content
    assert "window.jsyaml.dump" in content
    assert "/api/template/" in content and "/normalized'" in content
    assert "/api/template/" in content and "/normalized'" in content
    assert "/api/preview/template/raw?return_format=base64" in content
    assert 'id="collapseDesignerTemplateSource" class="panel-collapse collapse"' in content


def test_backend_exposes_template_designer_schema_api_and_page_route():
    content = APP_FILE.read_text(encoding="utf-8")

    assert '@route("/templatedesigner")' in content
    assert "@route('/api/template/designer/schema'" in content
    assert "@route('/api/preview/template/raw'" in content
    assert 'def build_template_designer_schema():' in content
    assert "template_data_values = body.get('template_data', {})" in content


def test_schema_hides_default_submit_button():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import build_template_designer_schema

    payload = build_template_designer_schema()
    ui_schema = payload.get('uiSchema', {})
    submit_options = ui_schema.get('ui:submitButtonOptions', {})
    assert submit_options.get('norender') is True


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


def test_plugin_widgets_js_endpoint_exists_in_app():
    content = APP_FILE.read_text(encoding="utf-8")
    assert "@route('/api/template/designer/widgets.js'" in content
    assert 'get_plugin_widgets_js' in content


def test_image_file_element_contributes_widget_and_ui_schema():
    """ImageFileElement must define both get_widget_js() and get_ui_schema()."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from elements.ImageFile import ImageFileElement

    ui = ImageFileElement.get_ui_schema()
    assert 'file' in ui, "ImageFileElement.get_ui_schema() must define 'file'"
    assert 'ui:widget' in ui['file'], "'file' must specify a ui:widget"

    js = ImageFileElement.get_widget_js()
    assert js and js.strip(), "ImageFileElement.get_widget_js() must return non-empty JS"
    widget_name = ui['file']['ui:widget']
    assert widget_name in js, f"Widget JS must register '{widget_name}'"


def test_element_base_get_plugin_widgets_js_wraps_iife():
    """get_plugin_widgets_js() output must be a safe IIFE — no bare eval."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from elements import ElementBase
    js = ElementBase.get_plugin_widgets_js()
    assert 'registerWidget' in js
    assert '(function' in js
    assert 'eval' not in js


def test_element_base_get_plugin_ui_schema_includes_image_file_widget():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from elements import ElementBase
    merged = ElementBase.get_plugin_ui_schema()
    assert 'file' in merged, "Merged uiSchema must include 'file' from ImageFileElement"


def test_schema_uses_named_element_options_and_hides_fixed_type_field():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import build_template_designer_schema

    payload = build_template_designer_schema()
    schema = payload['schema']
    element_items = schema['properties']['elements']['items']
    one_of = element_items.get('oneOf', [])

    assert one_of, "Elements oneOf options should be present"
    titles = [option.get('title') for option in one_of if isinstance(option, dict)]
    if 'Basic' in titles and len(titles) > 1:
        assert titles[-1] == 'Basic', f"Basic should be last in top-level selector, got {titles}"
    for option in one_of:
        assert option.get('title'), "Each oneOf option should have a friendly title"
        type_prop = option.get('properties', {}).get('type', {})
        assert type_prop.get('const') or type_prop.get('enum'), "Each oneOf option should declare a fixed type"

    definitions = schema.get('definitions', {})
    for def_schema in definitions.values():
        props = def_schema.get('properties', {})
        if 'type' in props:
            type_prop = props['type']
            assert isinstance(type_prop, dict), "Type discriminator must be an object schema"
            assert type_prop.get('enum') and len(type_prop['enum']) == 1, "Fixed type should be represented as a single-value enum"


def test_nested_elements_have_type_discriminators():
    """Nested-capable elements should expose child selector branches keyed by explicit type."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import build_template_designer_schema

    payload = build_template_designer_schema()
    definitions = payload['schema']['definitions']

    nested_keys = ['json_api', 'from_json_payload', 'grocy_entry', 'data_dict_item', 'data_array_index', 'inject_data', 'passthrough']
    for key in nested_keys:
        if key not in definitions:
            continue
        props = definitions[key].get('properties', {})
        elements_prop = props.get('elements')
        if not isinstance(elements_prop, dict):
            continue
        items = elements_prop.get('items', {})
        one_of = items.get('oneOf', [])
        assert isinstance(one_of, list) and one_of, f"Expected nested oneOf options for {key}"
        has_type_const = any(
            isinstance(option, dict)
            and isinstance(option.get('properties', {}).get('type'), dict)
            and (option['properties']['type'].get('const') or option['properties']['type'].get('enum'))
            for option in one_of
        )
        assert has_type_const, f"Expected child options with fixed type discriminators for {key}"


def test_nested_sample_objects_select_correct_schema_branches():
    """A small nested sample should resolve to the intended element branches, not basic."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import build_template_designer_schema

    schema = build_template_designer_schema()['schema']
    definitions = schema['definitions']

    sample = {
        'name': 'Nested Sample',
        'elements': [
            {
                'type': 'json_api',
                'endpoint': 'https://example.invalid/api',
                'method': 'get',
                'elements': [
                    {
                        'type': 'text',
                        'name': 'Nested Text',
                        'key': 'nested_text',
                        'horizontal_offset': 0,
                        'vertical_offset': 0
                    }
                ]
            }
        ]
    }

    def resolve_schema_key_for_object(node_schema, obj):
        options = node_schema.get('oneOf') or node_schema.get('anyOf') or []
        assert options, f"No oneOf/anyOf options available for object: {obj}"

        chosen = None
        for option in options:
            if option.get('type') != 'object':
                continue
            props = option.get('properties', {})
            type_prop = props.get('type', {})
            const_value = type_prop.get('const')
            if const_value is None:
                enum_values = type_prop.get('enum', [])
                if isinstance(enum_values, list) and len(enum_values) == 1:
                    const_value = enum_values[0]
            if const_value == obj.get('type'):
                chosen = option
                break

        assert chosen is not None, f"Could not resolve branch for object type={obj.get('type')}"
        type_prop = chosen.get('properties', {}).get('type', {})
        schema_key = type_prop.get('const')
        if schema_key is None:
            enum_values = type_prop.get('enum', [])
            if isinstance(enum_values, list) and len(enum_values) == 1:
                schema_key = enum_values[0]
        assert schema_key in definitions, f"Resolved option type={schema_key} is missing a definition"
        return schema_key, definitions[schema_key]

    top_elements_schema = schema['properties']['elements']
    top_item_schema = top_elements_schema['items']
    top_key, top_schema = resolve_schema_key_for_object(top_item_schema, sample['elements'][0])
    assert top_key == 'json_api'
    assert top_key != 'basic'

    child_schema = definitions[top_key]['properties']['elements']['items']
    child_key, _ = resolve_schema_key_for_object(child_schema, sample['elements'][0]['elements'][0])
    assert child_key == 'text'
    assert child_key != 'basic'


def test_nested_template_round_trips_through_generated_source_preserving_types():
    """Nested template data should round-trip through JSON and YAML source formats."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import yaml

    template = {
        'name': 'Round Trip Sample',
        'elements': [
            {
                'type': 'json_api',
                'endpoint': 'https://example.invalid/api',
                'method': 'get',
                'elements': [
                    {
                        'type': 'text',
                        'name': 'Nested Text',
                        'key': 'nested_text',
                        'horizontal_offset': 0,
                        'vertical_offset': 0
                    },
                    {
                        'type': 'image_file',
                        'name': 'Nested Image',
                        'file': '/appconfig/images/sample.png',
                        'position': [0, 0, 100, 100]
                    }
                ]
            }
        ]
    }

    def nested_types(data):
        types = []

        def walk(node):
            if isinstance(node, dict):
                if 'type' in node:
                    types.append(node['type'])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        return types

    for serializer, deserializer in (
        (lambda obj: json.dumps(obj, indent=2, sort_keys=False), json.loads),
        (lambda obj: yaml.safe_dump(obj, sort_keys=False), yaml.safe_load),
    ):
        generated_source = serializer(template)
        loaded = deserializer(generated_source)

        assert loaded['elements'][0]['type'] == 'json_api'
        assert loaded['elements'][0]['elements'][0]['type'] == 'text'
        assert loaded['elements'][0]['elements'][1]['type'] == 'image_file'
        assert nested_types(loaded) == nested_types(template)


def test_basic_branch_is_last_in_nested_selector_options():
    """The generic basic option should be last so specific branches are chosen first."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import build_template_designer_schema

    schema = build_template_designer_schema()['schema']
    definitions = schema['definitions']

    for key, def_schema in definitions.items():
        props = def_schema.get('properties', {})
        elements_prop = props.get('elements')
        if not isinstance(elements_prop, dict):
            continue
        items = elements_prop.get('items', {})
        options = items.get('oneOf', [])
        if not options:
            continue
        titles = [opt.get('title') for opt in options if isinstance(opt, dict)]
        if 'Basic' in titles and len(titles) > 1:
            assert titles[-1] == 'Basic', f"Basic should be last for {key}, got {titles}"


def test_normalization_uses_declared_type_only():
    """Type normalization should preserve explicit type values and avoid shape-based rewrites."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from brother_ql_web import normalize_template_data

    template = {
        'name': 'Type Priority',
        'elements': [
            {
                'type': 'text',
                # Endpoint belongs to json_api shape, but declared type must win.
                'endpoint': 'https://example.invalid/api',
                'name': 'Still Text',
                'key': 'my_key'
            }
        ]
    }

    normalized = normalize_template_data(template)
    assert normalized['elements'][0]['type'] == 'text'


def test_loaded_nested_template_uses_normalized_endpoint_without_client_rewrite():
    """Loaded templates should come from the normalized endpoint and use the parsed payload directly."""
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert "url: '/api/template/' + encodeURIComponent(templateName) + '/normalized'" in content
    assert 'currentFormData = parsed;' in content
    assert 'normalizeLoadedTemplateTypes' not in content


def test_client_prioritizes_schema_branch_from_explicit_type():
    """Designer UI should prioritize oneOf/anyOf options using the element's explicit type."""
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert 'function getFixedOptionType(option)' in content
    assert 'function prioritizeTypeDiscriminatedOptions(schemaNode, dataNode)' in content
    assert 'getFixedOptionType(a) === nodeType' in content
    assert 'schema: buildRenderSchema()' in content
    assert 'var sampleItem = dataNode.length > 0 ? dataNode[0] : null;' in content
    assert 'prioritizeTypeDiscriminatedOptions(schemaNode.items, sampleItem);' in content


def test_designer_has_collapsible_sections_and_compact_array_toolbar():
    """Designer UI should support collapsible object sections and a compact array-item toolbox."""
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert 'function ObjectFieldTemplate(props)' in content
    assert 'className: \'rjsf-collapsible-object\'' in content
    assert 'buildSectionSummary(props)' in content
    assert 'ObjectFieldTemplate: ObjectFieldTemplate' in content
    assert 'function ArrayFieldTemplate(props)' in content
    assert 'ArrayFieldTemplate: ArrayFieldTemplate' in content
    assert '#designerFormMount .rjsf-array-item-actions' in content
    assert "'data-rjsf-object-id': id" in content
    assert "'__oneof_select, #'" in content
    assert 'rjsf-collapsible-arrow glyphicon glyphicon-chevron-right' in content
    assert "createCollapsibleSection('Template Settings'" in content
    assert 'function syncCollapsedTypePickers()' in content


def test_designer_uses_print_like_three_column_collapsible_side_sections():
    """Designer should keep side-column widths and collapsible section style aligned with template print UX."""
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert content.count('class="col-md-4"') >= 2
    assert 'class="col-md-6"' in content
    assert '#designerLayoutRow' in content
    assert 'Template File' in content
    assert 'Template Source (.lbl)' in content
    assert 'Template Data' in content
    assert 'href="#collapseDesignerTemplateFile"' in content
    assert 'href="#collapseDesignerTemplateSource"' in content
    assert 'href="#collapseDesignerTemplateData"' in content
    assert 'href="#collapseDesignerPreview"' in content
    assert 'href="#collapseDesignerStatus"' in content


def test_preview_printer_change_updates_label_sizes_like_print_page():
    """Designer preview should refresh label sizes from printer media endpoint when printer selection changes."""
    content = DESIGNER_VIEW.read_text(encoding="utf-8")

    assert "url: '/api/printer/' + encodeURIComponent(printerName) + '/media'" in content
    assert "$('#previewPrinter').on('change'" in content
    assert 'updatePreviewLabelSizes($(this).val()' in content
    assert 'template_data: templateDataPayload' in content

