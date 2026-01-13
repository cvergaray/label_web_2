import unittest
from PIL import Image
import elements

# Ensure plugins are loaded
# elements.__init__ loads modules on import

class TestInjectData(unittest.TestCase):
    def setUp(self):
        self.injector = None
        # Find the InjectData plugin class
        for plugin in elements.ElementBase.plugins:
            if getattr(plugin, 'can_process', None) and plugin.can_process({'type': 'inject_data'}):
                self.injector = plugin()
                break
        self.assertIsNotNone(self.injector, "InjectData plugin not found")
        # Minimal image for processing
        self.im = Image.new('RGB', (10, 10))
        self.margins = (0, 0)
        self.dimensions = (10, 10)

    def test_inject_payload_no_override(self):
        element = {
            'type': 'inject_data',
            'target_key': 'foo',
            'data': 'bar',
            'target': 'payload',
            'override': False
        }
        payload = {}
        kwargs = {}
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)
        self.assertEqual(payload.get('foo'), 'bar')
        # existing value should not be overridden
        payload['foo'] = 'existing'
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)
        self.assertEqual(payload.get('foo'), 'existing')

    def test_inject_kwargs_runs(self):
        # Ensure the injector runs without error when targeting kwargs
        element = {
            'type': 'inject_data',
            'target_key': 'font_size',
            'data': 12,
            'target': 'kwargs',
            'override': True
        }
        payload = {}
        kwargs = {'font_size': 40}
        # Should not raise
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)

    def test_inject_children(self):
        children = [
            {'type': 'text', 'name': 'Child 1'},
            {'type': 'text', 'name': 'Child 2', 'datakey': 'already'},
            'non-dict-child-ignored'
        ]
        element = {
            'type': 'inject_data',
            'target_key': 'datakey',
            'data': 'title',
            'target': 'children',
            'override': False,
            'elements': children
        }
        payload = {}
        kwargs = {}
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)
        # ensure dict children got updated according to override behavior
        self.assertEqual(element['elements'][0].get('datakey'), 'title')
        # second child already had datakey; since override False, it should remain unchanged
        self.assertEqual(element['elements'][1].get('datakey'), 'already')
        # non-dict child should remain as-is
        self.assertEqual(element['elements'][2], 'non-dict-child-ignored')

    def test_inject_children_override_true(self):
        children = [
            {'type': 'text', 'name': 'Child 1', 'datakey': 'old'},
            {'type': 'text', 'name': 'Child 2', 'datakey': 'already'}
        ]
        element = {
            'type': 'inject_data',
            'target_key': 'datakey',
            'data': 'new_value',
            'target': 'children',
            'override': True,
            'elements': children
        }
        payload = {}
        kwargs = {}
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)
        # Both children should be overwritten
        self.assertEqual(element['elements'][0].get('datakey'), 'new_value')
        self.assertEqual(element['elements'][1].get('datakey'), 'new_value')

    def test_unknown_target_no_crash(self):
        element = {
            'type': 'inject_data',
            'target_key': 'foo',
            'data': 'bar',
            'target': 'unknown_target',
            'override': False,
            'elements': [ {'type': 'text', 'name': 'Child'} ]
        }
        payload = {}
        kwargs = {}
        # Should not raise even with unknown target
        self.injector.process_element(element, self.im, self.margins, self.dimensions, payload, **kwargs)
        # Ensure children still processed
        self.assertTrue(isinstance(element.get('elements'), list))

    def test_kwargs_downstream_with_controlled_element(self):
        # Create a lightweight test plugin that reads from kwargs using ElementBase.get_value
        called_flag = {'called': False}
        class KwargsReader(elements.ElementBase):
            @staticmethod
            def can_process(el):
                return el.get('type') == 'kwargs_reader'
            def process_element(self, el, im, margins, dimensions, payload, **kwargs):
                called_flag['called'] = True
                # Read a value from kwargs or element fallback
                read_key = el.get('read_key', 'sample')
                expected = el.get('expected')
                value = self.get_value(el, kwargs, read_key)
                # Assert inside processing; in a real plugin, we'd perhaps write to payload
                assert value == expected, f"Expected {expected}, got {value}"
                return im
        # Register the test plugin temporarily
        plugins = elements.ElementBase.plugins
        plugins.append(KwargsReader)
        try:
            # Inject into kwargs then process controlled element as a child to receive modified kwargs
            inject_kwargs_element = {
                'type': 'inject_data',
                'target_key': 'sample',
                'data': 'from_kwargs',
                'target': 'kwargs',
                'override': True,
                'elements': [
                    {
                        'type': 'kwargs_reader',
                        'read_key': 'sample',
                        'expected': 'from_kwargs'
                    }
                ]
            }
            payload = {}
            kwargs = {}
            # Run injector which will also process its child with modified kwargs
            self.injector.process_element(inject_kwargs_element, self.im, self.margins, self.dimensions, payload, **kwargs)
            # Ensure the downstream element was processed
            self.assertTrue(called_flag['called'], "Downstream kwargs_reader element was not processed")
        finally:
            # Ensure the test plugin does not pollute the global plugin registry
            if KwargsReader in plugins:
                plugins.remove(KwargsReader)
if __name__ == '__main__':
    unittest.main()
