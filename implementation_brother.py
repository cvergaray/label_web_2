from brother_ql.devicedependent import models, label_type_specs, label_sizes
from brother_ql.devicedependent import ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL
from brother_ql import BrotherQLRaster, create_label
from brother_ql.backends import backend_factory, guess_backend

class implementation:

    def __init__(self):
        #Common Properties
        self.DEBUG = False
        self.CONFIG = None
        self.logger = None
        
        #Implementation-Specific Properties
        self.BACKEND_CLASS = None
        
    def initialize(self):
        error = ''
        try:
            selected_backend = guess_backend(self.CONFIG['PRINTER']['PRINTER'])
        except ValueError:
            error = "Couln't guess the backend to use from the printer string descriptor"
        self.BACKEND_CLASS = backend_factory(selected_backend)['backend_class']        
        
        return error
    
    def get_label_sizes(self):
        return [ (name, label_type_specs[name]['name']) for name in label_sizes]
        
    def get_default_label_size():
        return "62"
        
    def get_label_kind(self, label_size_description):
        return label_type_specs[label_size_description]['kind']

    def get_label_dimensions(self, label_size):
        try:
            ls = label_type_specs[label_size]
        except KeyError:
            raise LookupError("Unknown label_size")
        return ls['dots_printable']
        
    def get_label_width_height(self, textsize, **kwargs):
        label_type = kwargs['kind']
        width, height = kwargs['width'], kwargs['height']
        if kwargs['orientation'] == 'standard':
            if label_type in (ENDLESS_LABEL,):
                height = textsize[1] + kwargs['margin_top'] + kwargs['margin_bottom']
        elif kwargs['orientation'] == 'rotated':
            if label_type in (ENDLESS_LABEL,):
                width = textsize[0] + kwargs['margin_left'] + kwargs['margin_right']
        return width, height
        
    def get_label_offset(self, calculated_width, calculated_height, textsize, **kwargs):
        label_type = kwargs['kind']
        if kwargs['orientation'] == 'standard':
            if label_type in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
                vertical_offset  = (calculated_height - textsize[1])//2
                vertical_offset += (kwargs['margin_top'] - kwargs['margin_bottom'])//2
            else:
                vertical_offset = kwargs['margin_top']
            horizontal_offset = max((calculated_width - textsize[0])//2, 0)
        elif kwargs['orientation'] == 'rotated':
            vertical_offset  = (calculated_height - textsize[1])//2
            vertical_offset += (kwargs['margin_top'] - kwargs['margin_bottom'])//2
            if label_type in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
                horizontal_offset = max((calculated_width - textsize[0])//2, 0)
            else:
                horizontal_offset = kwargs['margin_left']
        offset = horizontal_offset, vertical_offset        
        return offset
        
    def print_label(self, im, **context):
        return_dict = {'success' : False }
        
        if context['kind'] == ENDLESS_LABEL:
            rotate = 0 if context['orientation'] == 'standard' else 90
        elif context['kind'] in (ROUND_DIE_CUT_LABEL, DIE_CUT_LABEL):
            rotate = 'auto'

        qlr = BrotherQLRaster(self.CONFIG['PRINTER']['MODEL'])
        red = False
        if 'red' in context['label_size']:
            red = True

        create_label(qlr, im, context['label_size'], red=red, threshold=context['threshold'], cut=True, rotate=rotate)

        if not self.DEBUG:
            try:
                be = self.BACKEND_CLASS(self.CONFIG['PRINTER']['PRINTER'])
                be.write(qlr.data)
                be.dispose()
                del be
            except Exception as e:
                return_dict['message'] = str(e)
                self.logger.warning('Exception happened: %s', e)
                return return_dict
        
        return_dict['success'] = True
        if self.DEBUG: return_dict['data'] = str(qlr.data)
        
        return return_dict