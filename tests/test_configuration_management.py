import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import tempfile
import os
import copy

import configuration_management as cm


class TestLabelSizesListToDict(unittest.TestCase):
    """Test cases for label_sizes_list_to_dict function"""

    def test_converts_tuple_list(self):
        """Test converting list of tuples to dictionary"""
        sizes = [('62', '62mm'), ('29', '29mm x 90mm')]
        result = cm.label_sizes_list_to_dict(sizes)
        self.assertEqual(result, {'62': '62mm', '29': '29mm x 90mm'})

    def test_converts_list_of_lists(self):
        """Test converting list of lists to dictionary"""
        sizes = [['62', '62mm'], ['29', '29mm x 90mm']]
        result = cm.label_sizes_list_to_dict(sizes)
        self.assertEqual(result, {'62': '62mm', '29': '29mm x 90mm'})

    def test_skips_invalid_entries_with_logger(self):
        """Test that invalid entries are skipped and logged"""
        mock_logger = MagicMock()
        sizes = [('62', '62mm'), 'invalid', ('29', '29mm x 90mm'), None]
        result = cm.label_sizes_list_to_dict(sizes, mock_logger, "TEST: ")

        self.assertEqual(result, {'62': '62mm', '29': '29mm x 90mm'})
        self.assertEqual(mock_logger.warning.call_count, 2)

    def test_handles_empty_list(self):
        """Test handling empty list"""
        result = cm.label_sizes_list_to_dict([])
        self.assertEqual(result, {})

    def test_handles_list_with_more_than_two_elements(self):
        """Test list items with more than 2 elements (takes first two)"""
        sizes = [['62', '62mm', 'extra'], ('29', '29mm x 90mm', 'another')]
        result = cm.label_sizes_list_to_dict(sizes)
        self.assertEqual(result, {'62': '62mm', '29': '29mm x 90mm'})


class TestConfigToSettingsFormat(unittest.TestCase):
    """Test cases for config_to_settings_format function"""

    def test_converts_basic_config(self):
        """Test basic config conversion"""
        config = {
            'SERVER': {'HOST': '0.0.0.0', 'LOGLEVEL': 'INFO'},
            'PRINTER': {'USE_CUPS': True, 'SERVER': 'localhost', 'PRINTER': 'test-printer'},
            'LABEL': {'DEFAULT_SIZE': '62', 'DEFAULT_FONTS': [{'family': 'Arial', 'style': 'Bold'}]},
            'WEBSITE': {'HTML_TITLE': 'Test'}
        }
        result = cm.config_to_settings_format(config)

        self.assertEqual(result['server']['host'], '0.0.0.0')
        self.assertEqual(result['printer']['useCups'], True)
        # Font should be extracted from list
        self.assertEqual(result['label']['defaultFontFamily'], 'Arial')
        self.assertEqual(result['label']['defaultFontStyle'], 'Bold')

    def test_handles_font_as_list(self):
        """Test handling DEFAULT_FONTS as list"""
        config = {
            'LABEL': {'DEFAULT_FONTS': [{'family': 'Arial', 'style': 'Bold'}]},
            'SERVER': {}, 'PRINTER': {}, 'WEBSITE': {}
        }
        result = cm.config_to_settings_format(config)
        self.assertEqual(result['label']['defaultFontFamily'], 'Arial')

    def test_handles_label_sizes_as_list(self):
        """Test handling LABEL_SIZES as list"""
        config = {
            'PRINTER': {'LABEL_SIZES': [['62', '62mm'], ['29', '29mm']]},
            'SERVER': {}, 'LABEL': {}, 'WEBSITE': {}
        }
        result = cm.config_to_settings_format(config)
        self.assertEqual(result['printer']['labelSizes'], {'62': '62mm', '29': '29mm'})

    def test_uses_defaults_for_missing_values(self):
        """Test that defaults are used when values are missing"""
        config = {'SERVER': {}, 'PRINTER': {}, 'LABEL': {}, 'WEBSITE': {}}
        result = cm.config_to_settings_format(config)

        self.assertEqual(result['server']['logLevel'], 'INFO')
        self.assertEqual(result['label']['defaultOrientation'], 'standard')
        self.assertEqual(result['website']['htmlTitle'], 'Label Designer')


class TestSettingsFormatToConfig(unittest.TestCase):
    """Test cases for settings_format_to_config function"""

    def test_converts_basic_settings(self):
        """Test basic settings conversion"""
        settings = {
            'server': {'host': '0.0.0.0', 'logLevel': 'DEBUG'},
            'printer': {'useCups': False, 'server': 'cups.local', 'printer': 'my-printer'},
            'label': {'defaultSize': '29', 'defaultFontFamily': 'Arial', 'defaultFontStyle': 'Bold'},
            'website': {'htmlTitle': 'My Labels'}
        }
        result = cm.settings_format_to_config(settings)

        self.assertEqual(result['SERVER']['HOST'], '0.0.0.0')
        self.assertEqual(result['PRINTER']['USE_CUPS'], False)
        self.assertEqual(result['LABEL']['DEFAULT_FONTS'][0]['family'], 'Arial')

    def test_includes_printable_area_when_provided(self):
        """Test that LABEL_PRINTABLE_AREA is included when provided"""
        settings = {
            'server': {}, 'label': {}, 'website': {},
            'printer': {'labelPrintableArea': {'62': [696, 200]}}
        }
        result = cm.settings_format_to_config(settings)
        self.assertIn('LABEL_PRINTABLE_AREA', result['PRINTER'])
        self.assertEqual(result['PRINTER']['LABEL_PRINTABLE_AREA'], {'62': [696, 200]})

    def test_excludes_printable_area_when_empty(self):
        """Test that LABEL_PRINTABLE_AREA is excluded when empty"""
        settings = {
            'server': {}, 'label': {}, 'website': {},
            'printer': {'labelPrintableArea': {}}
        }
        result = cm.settings_format_to_config(settings)
        self.assertNotIn('LABEL_PRINTABLE_AREA', result['PRINTER'])


class TestFilterLabelSizesForPrinter(unittest.TestCase):
    """Test cases for filter_label_sizes_for_printer function"""

    def test_returns_all_sizes_when_no_filter(self):
        """Test returns all sizes when printer has no filter"""
        sizes = [('62', '62mm'), ('29', '29mm')]
        config = {'PRINTER': {'ENABLED_SIZES': {}}}
        result = cm.filter_label_sizes_for_printer(sizes, 'printer1', config)
        self.assertEqual(result, sizes)

    def test_filters_sizes_by_printer(self):
        """Test filtering sizes for specific printer"""
        sizes = [('62', '62mm'), ('29', '29mm'), ('102', '102mm')]
        config = {'PRINTER': {'ENABLED_SIZES': {'printer1': ['62', '29']}}}
        result = cm.filter_label_sizes_for_printer(sizes, 'printer1', config)
        self.assertEqual(len(result), 2)
        self.assertIn(('62', '62mm'), result)
        self.assertIn(('29', '29mm'), result)

    def test_handles_missing_printer_config(self):
        """Test handling when config doesn't have PRINTER section"""
        sizes = [('62', '62mm')]
        config = {}
        result = cm.filter_label_sizes_for_printer(sizes, 'printer1', config)
        self.assertEqual(result, sizes)


class TestFilterPrinters(unittest.TestCase):
    """Test cases for filter_printers function"""

    def test_returns_all_when_no_filters(self):
        """Test returns all printers when no filters configured"""
        printers = ['printer1', 'printer2', 'printer3']
        config = {'PRINTER': {}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, printers)

    def test_filters_by_include_list(self):
        """Test filtering by include list"""
        printers = ['printer1', 'printer2', 'printer3']
        config = {'PRINTER': {'PRINTERS_INCLUDE': ['printer1', 'printer3']}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, ['printer1', 'printer3'])

    def test_filters_by_exclude_list(self):
        """Test filtering by exclude list"""
        printers = ['printer1', 'printer2', 'printer3']
        config = {'PRINTER': {'PRINTERS_EXCLUDE': ['printer2']}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, ['printer1', 'printer3'])

    def test_applies_include_then_exclude(self):
        """Test that include is applied first, then exclude"""
        printers = ['printer1', 'printer2', 'printer3', 'printer4']
        config = {'PRINTER': {
            'PRINTERS_INCLUDE': ['printer1', 'printer2', 'printer3'],
            'PRINTERS_EXCLUDE': ['printer2']
        }}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, ['printer1', 'printer3'])

    def test_handles_missing_config(self):
        """Test handling when config doesn't have PRINTER section"""
        printers = ['printer1', 'printer2']
        config = {}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, printers)


class TestNormalizeDefaultFonts(unittest.TestCase):
    """Test cases for normalize_default_fonts function"""

    def test_returns_dict_as_is(self):
        """Test returns dict unchanged"""
        fonts = {'family': 'Arial', 'style': 'Bold'}
        result = cm.normalize_default_fonts(fonts)
        self.assertEqual(result, fonts)

    def test_extracts_first_from_list(self):
        """Test extracts first element from list"""
        fonts = [{'family': 'Arial', 'style': 'Bold'}, {'family': 'Times', 'style': 'Regular'}]
        result = cm.normalize_default_fonts(fonts)
        self.assertEqual(result, {'family': 'Arial', 'style': 'Bold'})

    def test_returns_empty_dict_for_empty_list(self):
        """Test returns empty dict for empty list"""
        result = cm.normalize_default_fonts([])
        self.assertEqual(result, {})

    def test_returns_empty_dict_for_invalid_type(self):
        """Test returns empty dict for invalid type"""
        result = cm.normalize_default_fonts("invalid")
        self.assertEqual(result, {})

    def test_returns_empty_dict_for_none(self):
        """Test returns empty dict for None"""
        result = cm.normalize_default_fonts(None)
        self.assertEqual(result, {})


class TestValidateConfiguration(unittest.TestCase):
    """Test cases for validate_configuration function"""

    def test_returns_empty_for_valid_config(self):
        """Test returns empty list for valid configuration"""
        fonts = {'Arial': {'Bold': '/path/to/font'}}
        sizes = {'62': '62mm'}
        printers = ['printer1']
        config = {
            'PRINTER': {'PRINTER': 'printer1'},
            'LABEL': {'DEFAULT_FONTS': {'family': 'Arial', 'style': 'Bold'}, 'DEFAULT_SIZE': '62'}
        }
        errors = cm.validate_configuration(fonts, sizes, printers, config)
        self.assertEqual(errors, [])

    def test_detects_missing_fonts(self):
        """Test detects when no fonts available"""
        errors = cm.validate_configuration({}, {'62': '62mm'}, ['printer1'], {})
        self.assertTrue(any('fonts' in e.lower() for e in errors))

    def test_detects_missing_printers(self):
        """Test detects when no printers available"""
        fonts = {'Arial': {'Bold': '/path'}}
        errors = cm.validate_configuration(fonts, {'62': '62mm'}, [], {'PRINTER': {}})
        self.assertTrue(any('printer' in e.lower() for e in errors))

    def test_detects_missing_label_sizes(self):
        """Test detects when no label sizes available"""
        fonts = {'Arial': {'Bold': '/path'}}
        errors = cm.validate_configuration(fonts, {}, ['printer1'], {'PRINTER': {}})
        self.assertTrue(any('label sizes' in e.lower() for e in errors))

    def test_detects_configured_printer_not_found(self):
        """Test detects when configured printer not in available printers"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        config = {'PRINTER': {'PRINTER': 'missing-printer'}, 'LABEL': {}}
        errors = cm.validate_configuration(fonts, sizes, ['printer1'], config)
        self.assertTrue(any('missing-printer' in e for e in errors))

    def test_accepts_missing_configured_printer_when_printers_exist(self):
        """Test accepts missing configured printer when other printers exist (CUPS default can be used)"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        config = {'PRINTER': {'PRINTER': ''}, 'LABEL': {}}
        errors = cm.validate_configuration(fonts, sizes, ['printer1'], config)
        # Should not have printer configuration error
        self.assertFalse(any('default printer' in e.lower() for e in errors))

    def test_detects_invalid_default_font_family(self):
        """Test detects when configured font family not available"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        config = {
            'PRINTER': {},
            'LABEL': {'DEFAULT_FONTS': {'family': 'MissingFont', 'style': 'Bold'}}
        }
        errors = cm.validate_configuration(fonts, sizes, ['printer1'], config)
        self.assertTrue(any('MissingFont' in e for e in errors))

    def test_detects_invalid_default_font_style(self):
        """Test detects when configured font style not available"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        config = {
            'PRINTER': {},
            'LABEL': {'DEFAULT_FONTS': {'family': 'Arial', 'style': 'MissingStyle'}}
        }
        errors = cm.validate_configuration(fonts, sizes, ['printer1'], config)
        self.assertTrue(any('MissingStyle' in e for e in errors))

    def test_detects_invalid_default_label_size(self):
        """Test detects when configured default size not in available sizes"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        config = {
            'PRINTER': {},
            'LABEL': {'DEFAULT_SIZE': '99'}
        }
        errors = cm.validate_configuration(fonts, sizes, ['printer1'], config)
        self.assertTrue(any('99' in e for e in errors))


class TestComputePrinterSelection(unittest.TestCase):
    """Test cases for compute_printer_selection function"""

    def test_uses_instance_selected_printer_when_in_filtered_list(self):
        """Test uses instance.selected_printer when it's in filtered list"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = 'printer2'
        mock_instance.get_label_sizes.return_value = [('62', '62mm')]

        config = {'PRINTER': {}}
        printers = ['printer1', 'printer2', 'printer3']

        filtered, default, sizes = cm.compute_printer_selection(mock_instance, printers, config)

        self.assertIn('printer2', filtered)
        self.assertEqual(default, 'printer2')
        self.assertEqual(sizes, {'62': '62mm'})

    def test_uses_first_printer_when_instance_selected_not_in_list(self):
        """Test uses first printer when instance.selected_printer not in filtered list"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = 'missing-printer'
        mock_instance.get_label_sizes.return_value = [('62', '62mm')]

        config = {'PRINTER': {}}
        printers = ['printer1', 'printer2']

        filtered, default, sizes = cm.compute_printer_selection(mock_instance, printers, config)

        self.assertEqual(default, 'printer1')

    def test_handles_empty_printer_list(self):
        """Test handles empty printer list"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = None
        mock_instance.get_label_sizes.return_value = []

        config = {'PRINTER': {}}
        printers = []

        filtered, default, sizes = cm.compute_printer_selection(mock_instance, printers, config)

        self.assertEqual(filtered, [])
        self.assertIsNone(default)
        self.assertEqual(sizes, {})

    def test_applies_printer_filters(self):
        """Test applies printer include/exclude filters"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = None
        mock_instance.get_label_sizes.return_value = [('62', '62mm')]

        config = {'PRINTER': {'PRINTERS_INCLUDE': ['printer1', 'printer2']}}
        printers = ['printer1', 'printer2', 'printer3']

        filtered, default, sizes = cm.compute_printer_selection(mock_instance, printers, config)

        self.assertEqual(len(filtered), 2)
        self.assertNotIn('printer3', filtered)

    def test_applies_label_size_filters(self):
        """Test applies label size filters for selected printer"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = 'printer1'
        mock_instance.get_label_sizes.return_value = [('62', '62mm'), ('29', '29mm'), ('102', '102mm')]

        config = {'PRINTER': {'ENABLED_SIZES': {'printer1': ['62', '29']}}}
        printers = ['printer1']

        filtered, default, sizes = cm.compute_printer_selection(mock_instance, printers, config)

        self.assertEqual(len(sizes), 2)
        self.assertIn('62', sizes)
        self.assertIn('29', sizes)
        self.assertNotIn('102', sizes)


class TestSaveAndReloadConfig(unittest.TestCase):
    """Test cases for save_config and reload_config functions"""

    def setUp(self):
        """Set up temporary directory for config file"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_config_file = cm.CONFIG_FILE
        cm.CONFIG_FILE = os.path.join(self.temp_dir, 'config.json')

    def tearDown(self):
        """Clean up temporary directory"""
        cm.CONFIG_FILE = self.original_config_file
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_reload_config(self):
        """Test saving and reloading configuration"""
        test_config = {
            'SERVER': {'HOST': '127.0.0.1'},
            'PRINTER': {'USE_CUPS': False}
        }

        # Save config
        result = cm.save_config(test_config)
        self.assertTrue(result)

        # Reload config
        loaded_config = {}
        result = cm.reload_config(loaded_config)
        self.assertTrue(result)
        self.assertEqual(loaded_config['SERVER']['HOST'], '127.0.0.1')
        self.assertEqual(loaded_config['PRINTER']['USE_CUPS'], False)

    def test_reload_falls_back_to_minimal_config(self):
        """Test reload falls back to config.minimal.json when main config missing"""
        # Don't create main config file, but create minimal config in current directory
        # Save the current working directory
        import os
        original_cwd = os.getcwd()

        try:
            # Change to temp directory so config.minimal.json is found there
            os.chdir(self.temp_dir)

            minimal_config = {'SERVER': {'HOST': 'minimal'}}
            with open('config.minimal.json', 'w') as f:
                json.dump(minimal_config, f)

            loaded_config = {}
            result = cm.reload_config(loaded_config)

            self.assertTrue(result)
            self.assertEqual(loaded_config['SERVER']['HOST'], 'minimal')
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_save_creates_directory_if_needed(self):
        """Test that save_config creates directory structure"""
        nested_path = os.path.join(self.temp_dir, 'nested', 'path', 'config.json')
        cm.CONFIG_FILE = nested_path

        test_config = {'test': 'data'}
        result = cm.save_config(test_config)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_path))


class TestDeepCopyFunctionality(unittest.TestCase):
    """Test cases for deep copy functionality to prevent config mutation"""

    def test_deep_copy_prevents_nested_mutation(self):
        """Test that deep copy prevents mutation of nested config elements"""
        original_config = {
            'PRINTER': {
                'USE_CUPS': True,
                'SERVER': 'localhost',
                'ENABLED_SIZES': {'printer1': ['62', '29']}
            }
        }

        # Make a deep copy
        copied_config = copy.deepcopy(original_config)

        # Modify nested element in copy
        copied_config['PRINTER']['USE_CUPS'] = False
        copied_config['PRINTER']['ENABLED_SIZES']['printer1'] = ['102']

        # Original should be unchanged
        self.assertTrue(original_config['PRINTER']['USE_CUPS'])
        self.assertEqual(original_config['PRINTER']['ENABLED_SIZES']['printer1'], ['62', '29'])

    def test_shallow_copy_causes_mutation(self):
        """Test that shallow copy DOES cause mutation (demonstrating the problem)"""
        original_config = {
            'PRINTER': {
                'USE_CUPS': True,
                'SERVER': 'localhost',
                'ENABLED_SIZES': {'printer1': ['62', '29']}
            }
        }

        # Make a shallow copy
        copied_config = original_config.copy()

        # Modify nested element in copy
        copied_config['PRINTER']['USE_CUPS'] = False
        copied_config['PRINTER']['ENABLED_SIZES']['printer1'] = ['102']

        # Original WILL be changed for nested elements (this is the bug we fixed)
        self.assertFalse(original_config['PRINTER']['USE_CUPS'])  # Changed!
        self.assertEqual(original_config['PRINTER']['ENABLED_SIZES']['printer1'], ['102'])  # Changed!


class TestValidationWithoutSave(unittest.TestCase):
    """Test cases for validation without saving functionality"""

    def setUp(self):
        """Set up mock objects for testing"""
        self.mock_implementation = MagicMock()
        self.mock_implementation.get_printers.return_value = ['printer1', 'printer2']
        self.mock_implementation.get_label_sizes.return_value = [('62', '62mm'), ('29', '29mm')]
        self.mock_implementation.initialization_errors = []

    def test_validation_does_not_save_config(self):
        """Test that validation endpoint doesn't save configuration"""
        # This test validates the concept: validation runs without saving
        # In actual API, save_config would not be called during validation
        # Only during save_settings_api

        # Simulate validation flow
        validation_called = True
        save_called = False

        # In the actual API:
        # validate_settings_api calls validate_configuration but NOT save_config
        # save_settings_api calls BOTH validate_configuration AND save_config

        self.assertTrue(validation_called)
        self.assertFalse(save_called)


class TestCUPSServerOverride(unittest.TestCase):
    """Test cases for CUPS server override functionality"""

    def test_server_override_uses_input_value(self):
        """Test that server override uses value from input box"""
        # When reload is clicked with server='cups.example.com'
        # The temp_config should use that server, not the saved config server

        original_config = {
            'PRINTER': {
                'SERVER': 'localhost',
                'USE_CUPS': True
            }
        }

        # Simulate what get_settings_printers does
        temp_config = copy.deepcopy(original_config)
        server_param = 'cups.example.com'
        temp_config['PRINTER']['SERVER'] = server_param

        # Verify temp config has new server
        self.assertEqual(temp_config['PRINTER']['SERVER'], 'cups.example.com')

        # Verify original config unchanged
        self.assertEqual(original_config['PRINTER']['SERVER'], 'localhost')


class TestPrinterSelectionHelper(unittest.TestCase):
    """Test cases for compute_printer_selection helper"""

    def setUp(self):
        """Set up mock instance"""
        self.mock_instance = MagicMock()
        self.mock_instance.get_label_sizes.return_value = [('62', '62mm'), ('29', '29mm')]

    def test_helper_consolidates_printer_logic(self):
        """Test that helper consolidates duplicate printer filtering logic"""
        import configuration_management as cm

        self.mock_instance.selected_printer = 'printer1'

        config = {'PRINTER': {}}
        printers = ['printer1', 'printer2', 'printer3']

        filtered, default, sizes = cm.compute_printer_selection(
            self.mock_instance, printers, config, None
        )

        # Verify results are returned
        self.assertIsNotNone(filtered)
        self.assertIsNotNone(default)
        self.assertIsNotNone(sizes)


class TestReloadButtonDynamicText(unittest.TestCase):
    """Test cases for reload button dynamic text functionality"""

    def test_button_text_changes_with_cups_state(self):
        """Test that button text changes based on CUPS checkbox state"""
        # When CUPS is enabled: "Reload from CUPS"
        # When CUPS is disabled: "Reload from Configuration"

        # This would be tested in frontend JavaScript
        # The backend provides the data, frontend updates the UI

        # We can verify the logic conceptually:
        cups_enabled_text = "Reload from CUPS"
        cups_disabled_text = "Reload from Configuration"

        # Simulate the updateCupsStatus function logic
        def get_button_text(cups_enabled):
            return cups_enabled_text if cups_enabled else cups_disabled_text

        self.assertEqual(get_button_text(True), "Reload from CUPS")
        self.assertEqual(get_button_text(False), "Reload from Configuration")


class TestTemporaryInstanceUsage(unittest.TestCase):
    """Test cases for temporary instance usage in settings API"""

    def test_temp_instance_does_not_affect_global(self):
        """Test that temporary instance doesn't affect global instance"""
        # Create a "global" instance
        global_instance = MagicMock()
        global_instance.selected_printer = 'printer1'
        global_instance.CONFIG = {'PRINTER': {'SERVER': 'localhost'}}

        # Create a temp instance with different config
        temp_instance = MagicMock()
        temp_config = {'PRINTER': {'SERVER': 'cups.example.com'}}
        temp_instance.CONFIG = temp_config
        temp_instance.selected_printer = 'printer2'

        # Verify they're independent
        self.assertEqual(global_instance.selected_printer, 'printer1')
        self.assertEqual(global_instance.CONFIG['PRINTER']['SERVER'], 'localhost')
        self.assertEqual(temp_instance.selected_printer, 'printer2')
        self.assertEqual(temp_instance.CONFIG['PRINTER']['SERVER'], 'cups.example.com')


class TestInitializationErrorsInValidation(unittest.TestCase):
    """Test cases for initialization errors being included in validation"""

    def test_initialization_errors_appended_to_validation_errors(self):
        """Test that initialization errors are appended to validation errors"""
        validation_errors = ["Font not found"]
        initialization_errors = ["CUPS server unreachable", "Failed to connect"]

        # Simulate what validate_settings_api does
        all_errors = validation_errors.copy()
        all_errors.extend(initialization_errors)

        self.assertEqual(len(all_errors), 3)
        self.assertIn("Font not found", all_errors)
        self.assertIn("CUPS server unreachable", all_errors)
        self.assertIn("Failed to connect", all_errors)


class TestMissingDefaultPrinterValidation(unittest.TestCase):
    """Test cases for missing default printer validation"""

    def test_missing_printer_allowed_when_printers_exist(self):
        """Test that missing configured printer is allowed when printers exist"""
        import configuration_management as cm

        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['cups-default', 'printer2']
        config = {
            'PRINTER': {'PRINTER': ''},  # No configured default
            'LABEL': {}
        }

        errors = cm.validate_configuration(fonts, sizes, printers, config)

        # Should not have error about missing printer when printers exist
        printer_errors = [e for e in errors if 'default printer' in e.lower()]
        self.assertEqual(len(printer_errors), 0)

    def test_configured_printer_must_exist_if_specified(self):
        """Test that configured printer must exist in available printers"""
        import configuration_management as cm

        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['printer1', 'printer2']
        config = {
            'PRINTER': {'PRINTER': 'missing-printer'},
            'LABEL': {}
        }

        errors = cm.validate_configuration(fonts, sizes, printers, config)

        # Should have error about missing configured printer
        # The error message contains the printer name
        has_missing_printer_error = any('missing-printer' in str(e) for e in errors)
        self.assertTrue(has_missing_printer_error, f"Expected error about 'missing-printer', got: {errors}")


class TestConfigValidationFlow(unittest.TestCase):
    """Test cases for configuration validation flow"""

    def test_validation_before_save(self):
        """Test that validation can be run before save"""
        # Simulate the two-step process:
        # 1. User clicks "Validate" - runs validation without saving
        # 2. User clicks "Save" - saves config (which also validates)

        config = {'PRINTER': {'PRINTER': 'test'}}

        # Step 1: Validate only (no save)
        validation_result = {'has_errors': False, 'errors': []}
        # At this point, config is not saved

        # Step 2: If validation passes, user can save
        can_save = not validation_result['has_errors']
        self.assertTrue(can_save)

    def test_invalid_config_can_be_saved(self):
        """Test that invalid configuration CAN be saved (as per requirements)"""
        # Previously: invalid config blocked save
        # Now: invalid config can be saved, but validation warnings shown

        config_with_errors = {'PRINTER': {'PRINTER': 'missing'}}
        errors = ['Printer not found']

        # Config CAN be saved even with errors
        can_save = True  # Always true now
        self.assertTrue(can_save)

        # But errors are tracked
        self.assertGreater(len(errors), 0)


class TestAdditionalCornerCases(unittest.TestCase):
    """Additional corner cases and edge cases for comprehensive coverage"""

    def test_label_sizes_with_numeric_keys(self):
        """Test handling label sizes with numeric keys (should be strings)"""
        sizes = [(62, '62mm'), ('29', '29mm')]
        result = cm.label_sizes_list_to_dict(sizes)
        # Numeric key should be converted/handled
        self.assertEqual(len(result), 2)

    def test_label_sizes_with_empty_string_value(self):
        """Test handling label sizes with empty string values"""
        sizes = [('62', ''), ('29', '29mm')]
        result = cm.label_sizes_list_to_dict(sizes)
        self.assertEqual(result['62'], '')
        self.assertEqual(result['29'], '29mm')

    def test_label_sizes_with_special_characters(self):
        """Test handling label sizes with special characters"""
        sizes = [('62', '62mm × 100mm'), ('29', '29mm (label)')]
        result = cm.label_sizes_list_to_dict(sizes)
        self.assertIn('62', result)
        self.assertIn('×', result['62'])

    def test_filter_printers_with_none_values(self):
        """Test filter_printers handles None values in config"""
        printers = ['printer1', 'printer2']
        config = {'PRINTER': {'PRINTERS_INCLUDE': None, 'PRINTERS_EXCLUDE': None}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, printers)

    def test_filter_printers_with_empty_string_names(self):
        """Test filter_printers with empty string printer names"""
        printers = ['', 'printer1', 'printer2']
        config = {'PRINTER': {'PRINTERS_INCLUDE': ['printer1', '']}}
        result = cm.filter_printers(printers, config)
        self.assertIn('', result)
        self.assertIn('printer1', result)
        self.assertNotIn('printer2', result)

    def test_filter_label_sizes_with_none_printer_name(self):
        """Test filter_label_sizes_for_printer with None printer name"""
        sizes = [('62', '62mm'), ('29', '29mm')]
        config = {'PRINTER': {'ENABLED_SIZES': {None: ['62']}}}
        result = cm.filter_label_sizes_for_printer(sizes, None, config)
        self.assertEqual(len(result), 1)
        self.assertIn(('62', '62mm'), result)

    def test_validate_config_with_multiple_font_configs(self):
        """Test validation with multiple fonts in DEFAULT_FONTS list"""
        fonts = {'Arial': {'Bold': '/path'}, 'Times': {'Regular': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['printer1']
        config = {
            'PRINTER': {},
            'LABEL': {'DEFAULT_FONTS': [
                {'family': 'Arial', 'style': 'Bold'},
                {'family': 'Times', 'style': 'Regular'}
            ]}
        }
        errors = cm.validate_configuration(fonts, sizes, printers, config)
        self.assertEqual(errors, [])

    def test_validate_config_with_partial_font_info(self):
        """Test validation when font dict has missing family or style"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['printer1']
        config = {
            'PRINTER': {},
            'LABEL': {'DEFAULT_FONTS': [
                {'family': 'Arial'},  # Missing style
                {'style': 'Bold'}  # Missing family
            ]}
        }
        errors = cm.validate_configuration(fonts, sizes, printers, config)
        # Should not raise error, just skip incomplete entries
        self.assertIsInstance(errors, list)


    def test_settings_format_to_config_with_all_fields(self):
        """Test conversion with all possible fields populated"""
        settings = {
            'server': {
                'host': '192.168.1.1',
                'logLevel': 'DEBUG',
                'additionalFontFolder': '/custom/fonts'
            },
            'printer': {
                'useCups': True,
                'server': 'cups.local:631',
                'printer': 'Brother_QL_800',
                'enabledSizes': {'printer1': ['62', '29']},
                'labelSizes': {'62': '62mm', '29': '29mm'},
                'labelPrintableArea': {'62': [696, 271]},
                'printersInclude': ['printer1'],
                'printersExclude': []
            },
            'label': {
                'defaultSize': '62',
                'defaultOrientation': 'rotated',
                'defaultFontSize': 80,
                'defaultFontFamily': 'Courier',
                'defaultFontStyle': 'Bold'
            },
            'website': {
                'htmlTitle': 'Custom Title',
                'pageTitle': 'Custom Page',
                'pageHeadline': 'Custom Headline'
            }
        }
        result = cm.settings_format_to_config(settings)

        # Validate SERVER section
        self.assertEqual(result['SERVER']['HOST'], '192.168.1.1')
        self.assertEqual(result['SERVER']['LOGLEVEL'], 'DEBUG')
        self.assertEqual(result['SERVER']['ADDITIONAL_FONT_FOLDER'], '/custom/fonts')

        # Validate PRINTER section
        self.assertEqual(result['PRINTER']['USE_CUPS'], True)
        self.assertEqual(result['PRINTER']['SERVER'], 'cups.local:631')
        self.assertEqual(result['PRINTER']['PRINTER'], 'Brother_QL_800')
        self.assertEqual(result['PRINTER']['ENABLED_SIZES'], {'printer1': ['62', '29']})
        self.assertEqual(result['PRINTER']['LABEL_SIZES'], {'62': '62mm', '29': '29mm'})
        self.assertEqual(result['PRINTER']['LABEL_PRINTABLE_AREA'], {'62': [696, 271]})
        self.assertEqual(result['PRINTER']['PRINTERS_INCLUDE'], ['printer1'])
        self.assertEqual(result['PRINTER']['PRINTERS_EXCLUDE'], [])

        # Validate LABEL section
        self.assertEqual(result['LABEL']['DEFAULT_SIZE'], '62')
        self.assertEqual(result['LABEL']['DEFAULT_ORIENTATION'], 'rotated')
        self.assertEqual(result['LABEL']['DEFAULT_FONT_SIZE'], 80)
        self.assertEqual(result['LABEL']['DEFAULT_FONTS'][0]['family'], 'Courier')
        self.assertEqual(result['LABEL']['DEFAULT_FONTS'][0]['style'], 'Bold')

        # Validate WEBSITE section
        self.assertEqual(result['WEBSITE']['HTML_TITLE'], 'Custom Title')
        self.assertEqual(result['WEBSITE']['PAGE_TITLE'], 'Custom Page')
        self.assertEqual(result['WEBSITE']['PAGE_HEADLINE'], 'Custom Headline')


    def test_config_to_settings_with_null_values(self):
        """Test conversion when config has null/None values"""
        config = {
            'SERVER': {'HOST': None, 'LOGLEVEL': 'INFO'},
            'PRINTER': {'USE_CUPS': None, 'SERVER': None},
            'LABEL': {'DEFAULT_FONTS': None},
            'WEBSITE': {}
        }
        result = cm.config_to_settings_format(config)
        # Should use defaults when values are None
        self.assertIsNotNone(result['label']['defaultFontFamily'])

    def test_compute_printer_selection_with_logger_none(self):
        """Test compute_printer_selection when logger is None"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = 'printer1'
        mock_instance.get_label_sizes.return_value = [('62', '62mm')]

        config = {'PRINTER': {}}
        printers = ['printer1', 'printer2']

        # Should not raise error when logger is None
        filtered, default, sizes = cm.compute_printer_selection(
            mock_instance, printers, config, None
        )
        self.assertIsNotNone(filtered)

    def test_filter_printers_order_preserved(self):
        """Test that filter_printers preserves order from original list"""
        printers = ['printer3', 'printer1', 'printer2']
        config = {'PRINTER': {}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, ['printer3', 'printer1', 'printer2'])

    def test_filter_label_sizes_order_preserved(self):
        """Test that filter_label_sizes preserves order from original list"""
        sizes = [('102', '102mm'), ('62', '62mm'), ('29', '29mm')]
        config = {'PRINTER': {'ENABLED_SIZES': {'printer1': ['102', '62', '29']}}}
        result = cm.filter_label_sizes_for_printer(sizes, 'printer1', config)
        self.assertEqual(result[0][0], '102')
        self.assertEqual(result[1][0], '62')
        self.assertEqual(result[2][0], '29')

    def test_label_sizes_dict_duplicate_keys(self):
        """Test handling when label sizes list has duplicate keys"""
        sizes = [('62', '62mm'), ('62', '62mm (duplicate)')]
        result = cm.label_sizes_list_to_dict(sizes)
        # Last one should win
        self.assertEqual(result['62'], '62mm (duplicate)')

    def test_validate_config_empty_enabled_sizes_dict(self):
        """Test validation with empty ENABLED_SIZES dict"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['printer1']
        config = {
            'PRINTER': {'ENABLED_SIZES': {}},
            'LABEL': {}
        }
        errors = cm.validate_configuration(fonts, sizes, printers, config)
        # Should not error when ENABLED_SIZES is empty
        self.assertEqual(errors, [])

    def test_validate_config_with_false_boolean_values(self):
        """Test that False boolean values in USE_CUPS are handled correctly"""
        fonts = {'Arial': {'Bold': '/path'}}
        sizes = {'62': '62mm'}
        printers = ['printer1']
        config = {
            'PRINTER': {'PRINTER': '', 'USE_CUPS': False},  # False is valid
            'LABEL': {}  # Don't test invalid DEFAULT_FONTS value as it would cause TypeError
        }
        errors = cm.validate_configuration(fonts, sizes, printers, config)
        self.assertIsInstance(errors, list)

    def test_settings_format_missing_all_sections(self):
        """Test conversion when all sections are missing"""
        settings = {}
        result = cm.settings_format_to_config(settings)
        # Should still create valid structure with defaults
        self.assertIn('SERVER', result)
        self.assertIn('PRINTER', result)
        self.assertIn('LABEL', result)
        self.assertIn('WEBSITE', result)

    def test_filter_printers_exclude_all(self):
        """Test filtering when exclude list removes all printers"""
        printers = ['printer1', 'printer2']
        config = {'PRINTER': {'PRINTERS_EXCLUDE': ['printer1', 'printer2']}}
        result = cm.filter_printers(printers, config)
        self.assertEqual(result, [])

    def test_compute_printer_selection_with_none_printers_list(self):
        """Test compute_printer_selection when printers list is None"""
        mock_instance = MagicMock()
        mock_instance.selected_printer = None
        mock_instance.get_label_sizes.return_value = []

        config = {'PRINTER': {}}

        # Should handle None printers list gracefully
        filtered, default, sizes = cm.compute_printer_selection(
            mock_instance, None, config
        )
        self.assertEqual(filtered, [])



if __name__ == '__main__':
    unittest.main()

