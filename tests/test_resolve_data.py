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


if __name__ == '__main__':
    unittest.main()

