import unittest
import elements


class TestResolveData(unittest.TestCase):
    """Test cases for ElementBase.resolve_data method"""

    def setUp(self):
        """Set up test fixtures"""
        self.base = elements.ElementBase()

    def test_resolve_data_with_simple_data(self):
        """Test resolving data when only 'data' property is provided"""
        element = {'data': 'simple_value'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'simple_value')

    def test_resolve_data_with_none_data(self):
        """Test resolving data when data is None"""
        element = {'data': None}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertIsNone(result)

    def test_resolve_data_with_default_value(self):
        """Test resolving data with a default value when data is None"""
        element = {'data': None}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default_value')
        self.assertEqual(result, 'default_value')

    def test_resolve_data_with_key_from_kwargs(self):
        """Test resolving data using 'key' property from kwargs"""
        element = {'data': 'ignored', 'key': 'source_key'}
        kwargs = {'source_key': 'value_from_kwargs'}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'value_from_kwargs')

    def test_resolve_data_with_key_from_payload(self):
        """Test resolving data using 'key' property from payload when not in kwargs"""
        element = {'data': 'ignored', 'key': 'source_key'}
        kwargs = {}
        payload = {'source_key': 'value_from_payload'}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'value_from_payload')

    def test_resolve_data_with_key_prefers_kwargs(self):
        """Test that kwargs takes precedence over payload when both have the key"""
        element = {'data': 'ignored', 'key': 'source_key'}
        kwargs = {'source_key': 'from_kwargs'}
        payload = {'source_key': 'from_payload'}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'from_kwargs')

    def test_resolve_data_with_key_missing(self):
        """Test resolving data when key is not found in kwargs or payload"""
        element = {'data': 'fallback_data', 'key': 'missing_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        # Falls back to data when key not found
        self.assertEqual(result, 'fallback_data')

    def test_resolve_data_with_datakey_from_dict(self):
        """Test resolving data using 'datakey' to extract from nested dict"""
        element = {'data': {'nested': 'nested_value'}, 'datakey': 'nested'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'nested_value')

    def test_resolve_data_with_datakey_missing(self):
        """Test resolving data when datakey is not found in the dict"""
        element = {'data': {'nested': 'nested_value'}, 'datakey': 'missing'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertIsNone(result)

    def test_resolve_data_with_datakey_missing_and_default(self):
        """Test resolving data when datakey is not found but default is provided"""
        element = {'data': {'nested': 'nested_value'}, 'datakey': 'missing'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default_value')
        self.assertEqual(result, 'default_value')

    def test_resolve_data_with_datakey_non_dict_data(self):
        """Test resolving data when datakey is provided but data is not a dict"""
        element = {'data': 'not_a_dict', 'datakey': 'some_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertIsNone(result)

    def test_resolve_data_with_datakey_non_dict_data_and_default(self):
        """Test resolving data when datakey is provided, data is not a dict, and default is set"""
        element = {'data': 'not_a_dict', 'datakey': 'some_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='fallback')
        self.assertEqual(result, 'fallback')

    def test_resolve_data_with_key_and_datakey(self):
        """Test resolving data using both 'key' and 'datakey' together"""
        element = {
            'data': 'ignored',
            'key': 'source_key',
            'datakey': 'nested_field'
        }
        kwargs = {}
        payload = {'source_key': {'nested_field': 'extracted_value'}}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'extracted_value')

    def test_resolve_data_with_key_from_kwargs_and_datakey(self):
        """Test resolving data using both 'key' (from kwargs) and 'datakey' together"""
        element = {
            'data': 'ignored',
            'key': 'source_key',
            'datakey': 'nested_field'
        }
        kwargs = {'source_key': {'nested_field': 'extracted_from_kwargs'}}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'extracted_from_kwargs')

    def test_resolve_data_with_custom_base_key(self):
        """Test resolving data using a custom base_key"""
        element = {'custom_field': 'custom_value'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, base_key='custom_field')
        self.assertEqual(result, 'custom_value')

    def test_resolve_data_with_custom_base_key_and_key(self):
        """Test resolving data with custom base_key and 'key' property"""
        element = {
            'custom_field': 'ignored',
            'key': 'source_key'
        }
        kwargs = {'source_key': 'from_kwargs'}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, base_key='custom_field')
        self.assertEqual(result, 'from_kwargs')

    def test_resolve_data_with_custom_base_key_and_datakey(self):
        """Test resolving data with custom base_key and 'datakey' property"""
        element = {
            'custom_field': {'nested': 'nested_value'},
            'datakey': 'nested'
        }
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, base_key='custom_field')
        self.assertEqual(result, 'nested_value')

    def test_resolve_data_missing_base_key_property(self):
        """Test resolving data when the base_key property doesn't exist in element"""
        element = {'some_other_key': 'value'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertIsNone(result)

    def test_resolve_data_missing_base_key_property_with_default(self):
        """Test resolving data when base_key doesn't exist but default is provided"""
        element = {'some_other_key': 'value'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default')
        self.assertEqual(result, 'default')

    def test_resolve_data_with_numeric_data(self):
        """Test resolving data with numeric values"""
        element = {'data': 42}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 42)

    def test_resolve_data_with_boolean_data(self):
        """Test resolving data with boolean values"""
        element = {'data': True}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertTrue(result)

    def test_resolve_data_with_list_data(self):
        """Test resolving data with list values"""
        element = {'data': [1, 2, 3]}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, [1, 2, 3])

    def test_resolve_data_with_empty_dict_data(self):
        """Test resolving data with empty dict"""
        element = {'data': {}}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, {})

    def test_resolve_data_with_empty_dict_data_and_datakey(self):
        """Test resolving data with empty dict and datakey"""
        element = {'data': {}, 'datakey': 'missing_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default')
        self.assertEqual(result, 'default')

    def test_resolve_data_with_zero_value(self):
        """Test that zero is not treated as None/falsy"""
        element = {'data': 0}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default')
        self.assertEqual(result, 0)

    def test_resolve_data_with_empty_string(self):
        """Test that empty string is preserved"""
        element = {'data': ''}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default')
        self.assertEqual(result, '')

    def test_resolve_data_with_false_value(self):
        """Test that False value is preserved"""
        element = {'data': False}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, default='default')
        self.assertFalse(result)

    # Tests for kwarg_payload_key parameter
    def test_resolve_data_with_custom_kwarg_payload_key_from_kwargs(self):
        """Test resolving data using custom kwarg_payload_key from kwargs"""
        element = {'data': 'ignored', 'lookup_field': 'source_key'}
        kwargs = {'source_key': 'value_from_kwargs'}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        self.assertEqual(result, 'value_from_kwargs')

    def test_resolve_data_with_custom_kwarg_payload_key_from_payload(self):
        """Test resolving data using custom kwarg_payload_key from payload"""
        element = {'data': 'ignored', 'lookup_field': 'source_key'}
        kwargs = {}
        payload = {'source_key': 'value_from_payload'}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        self.assertEqual(result, 'value_from_payload')

    def test_resolve_data_with_custom_kwarg_payload_key_prefers_kwargs(self):
        """Test that custom kwarg_payload_key prefers kwargs over payload"""
        element = {'data': 'ignored', 'lookup_field': 'source_key'}
        kwargs = {'source_key': 'from_kwargs'}
        payload = {'source_key': 'from_payload'}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        self.assertEqual(result, 'from_kwargs')

    def test_resolve_data_with_custom_kwarg_payload_key_missing_property(self):
        """Test resolving data when custom kwarg_payload_key property doesn't exist in element"""
        element = {'data': 'fallback_data', 'some_other_field': 'value'}
        kwargs = {'source_key': 'ignored'}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        # Should fall back to data since lookup_field doesn't exist
        self.assertEqual(result, 'fallback_data')

    def test_resolve_data_with_custom_kwarg_payload_key_missing_in_kwargs_and_payload(self):
        """Test resolving data when custom kwarg_payload_key value not in kwargs or payload"""
        element = {'data': 'fallback_data', 'lookup_field': 'missing_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        # Should fall back to data when key not found
        self.assertEqual(result, 'fallback_data')

    def test_resolve_data_with_custom_kwarg_payload_key_and_datakey(self):
        """Test resolving data using custom kwarg_payload_key with datakey extraction"""
        element = {
            'data': 'ignored',
            'lookup_field': 'source_key',
            'datakey': 'nested_field'
        }
        kwargs = {}
        payload = {'source_key': {'nested_field': 'extracted_value'}}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        self.assertEqual(result, 'extracted_value')

    def test_resolve_data_with_custom_kwarg_payload_key_and_custom_base_key(self):
        """Test resolving data with both custom kwarg_payload_key and custom base_key"""
        element = {
            'source_data': 'ignored',
            'lookup_field': 'source_key'
        }
        kwargs = {'source_key': 'value_from_kwargs'}
        payload = {}

        result = self.base.resolve_data(
            element,
            kwargs,
            payload,
            base_key='source_data',
            kwarg_payload_key='lookup_field'
        )
        self.assertEqual(result, 'value_from_kwargs')

    def test_resolve_data_with_custom_kwarg_payload_key_and_custom_base_key_with_datakey(self):
        """Test resolving data with custom kwarg_payload_key, custom base_key, and datakey"""
        element = {
            'source_data': 'ignored',
            'lookup_field': 'source_key',
            'datakey': 'nested'
        }
        kwargs = {'source_key': {'nested': 'extracted_via_lookup'}}
        payload = {}

        result = self.base.resolve_data(
            element,
            kwargs,
            payload,
            base_key='source_data',
            kwarg_payload_key='lookup_field'
        )
        self.assertEqual(result, 'extracted_via_lookup')

    def test_resolve_data_with_custom_kwarg_payload_key_none_value(self):
        """Test resolving data with custom kwarg_payload_key when the retrieved value is None"""
        element = {'data': 'fallback', 'lookup_field': 'source_key'}
        kwargs = {'source_key': None}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='lookup_field')
        # When key lookup returns None, should use default or data
        self.assertIsNone(result)

    def test_resolve_data_with_custom_kwarg_payload_key_and_default(self):
        """Test resolving data with custom kwarg_payload_key and default value"""
        element = {'data': None, 'lookup_field': 'missing_key'}
        kwargs = {}
        payload = {}

        result = self.base.resolve_data(
            element,
            kwargs,
            payload,
            default='default_value',
            kwarg_payload_key='lookup_field'
        )
        self.assertEqual(result, 'default_value')

    def test_resolve_data_with_custom_kwarg_payload_key_complex_scenario(self):
        """Test complex scenario: custom keys, nested data extraction, defaults"""
        element = {
            'user_source': {'profile': {'name': 'default_name'}, 'id': 123},
            'user_lookup': 'user_id',
            'datakey': 'profile'
        }
        kwargs = {}
        payload = {
            'user_id': {'profile': {'name': 'John Doe'}, 'id': 456}
        }

        result = self.base.resolve_data(
            element,
            kwargs,
            payload,
            base_key='user_source',
            kwarg_payload_key='user_lookup'
        )
        self.assertEqual(result, {'name': 'John Doe'})

    def test_resolve_data_with_custom_kwarg_payload_key_retrieves_dict(self):
        """Test that custom kwarg_payload_key can retrieve complex dict structures"""
        element = {
            'data': {},
            'config_key': 'settings'
        }
        expected_config = {
            'theme': 'dark',
            'language': 'en',
            'features': ['export', 'import']
        }
        kwargs = {'settings': expected_config}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='config_key')
        self.assertEqual(result, expected_config)

    def test_resolve_data_with_custom_kwarg_payload_key_retrieves_list(self):
        """Test that custom kwarg_payload_key can retrieve list structures"""
        element = {
            'data': [],
            'items_key': 'item_list'
        }
        expected_list = ['item1', 'item2', 'item3']
        kwargs = {'item_list': expected_list}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='items_key')
        self.assertEqual(result, expected_list)

    def test_resolve_data_custom_kwarg_payload_key_empty_string_property_name(self):
        """Test custom kwarg_payload_key with empty string (edge case)"""
        element = {'data': 'fallback_value', '': 'some_key'}
        kwargs = {'some_key': 'from_kwargs'}
        payload = {}

        # Empty string is a valid property name but won't be found by normal lookup
        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='')
        # Should return the value from the empty-string-named property key lookup
        self.assertEqual(result, 'from_kwargs')

    def test_resolve_data_default_kwarg_payload_key_is_key(self):
        """Test that default kwarg_payload_key parameter is 'key' (backward compatibility)"""
        element = {'data': 'ignored', 'key': 'username'}
        kwargs = {'username': 'john_doe'}
        payload = {}

        # Call without specifying kwarg_payload_key (should use default 'key')
        result = self.base.resolve_data(element, kwargs, payload)
        self.assertEqual(result, 'john_doe')

    def test_resolve_data_custom_kwarg_payload_key_with_numeric_values(self):
        """Test custom kwarg_payload_key with numeric values"""
        element = {'data': 0, 'value_key': 'count'}
        kwargs = {'count': 42}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='value_key')
        self.assertEqual(result, 42)

    def test_resolve_data_custom_kwarg_payload_key_with_boolean_values(self):
        """Test custom kwarg_payload_key with boolean values"""
        element = {'data': False, 'flag_key': 'is_active'}
        kwargs = {'is_active': True}
        payload = {}

        result = self.base.resolve_data(element, kwargs, payload, kwarg_payload_key='flag_key')
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()

