import elements

from PIL import Image
from elements.ImageElement.Element import element_image_base, get_base_definition


class ImageFileElement(elements.ElementBase):

    def __init__(self):
        pass

    @staticmethod
    def element_key():
        return 'image_file'

    @staticmethod
    def can_process(element):
        return element['type'] == ImageFileElement.element_key()

    def process_element(self, element, im, margins, dimensions, payload, **kwargs):
        try:
            file_path = element.get('file')

            print('loading image from ' + str(file_path))

            image = Image.open(file_path)
            if image is None:
                print("Error reading file!")
            im = element_image_base(image, element, im, margins, dimensions, **kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)

        return im

    @staticmethod
    def get_ui_schema():
        return {
            'file': {
                'ui:widget': 'imageFileSelector'
            }
        }

    @staticmethod
    def get_widget_js():
        return r"""registerWidget('imageFileSelector', function ImageFileSelectorWidget(props) {
  var imagesState   = React.useState([]); var images = imagesState[0]; var setImages = imagesState[1];
  var loadingState  = React.useState(true); var loading = loadingState[0]; var setLoading = loadingState[1];
  var uploadingState = React.useState(false); var uploading = uploadingState[0]; var setUploading = uploadingState[1];
  var errorState    = React.useState(null); var errorMsg = errorState[0]; var setErrorMsg = errorState[1];
  var value    = props.value || '';
  var disabled = props.disabled || false;

  function loadImageList() {
    setLoading(true);
    fetch('/api/images')
      .then(function(r) { return r.json(); })
      .then(function(data) { setImages(data.images || []); setLoading(false); })
      .catch(function() { setErrorMsg('Failed to load image list'); setLoading(false); });
  }
  React.useEffect(loadImageList, []);

  function handleSelect(e) { props.onChange(e.target.value || undefined); }

  function handleUpload(e) {
    var file = e.target.files[0];
    if (!file) return;
    setUploading(true); setErrorMsg(null);
    var fd = new FormData();
    fd.append('file', file);
    fetch('/api/images/upload', { method: 'POST', body: fd })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.success) { loadImageList(); props.onChange(data.path); }
        else { setErrorMsg(data.error || 'Upload failed'); }
        setUploading(false);
      })
      .catch(function() { setErrorMsg('Upload failed'); setUploading(false); });
  }

  return React.createElement('div', null,
    React.createElement('select', {
      className: 'form-control', id: props.id, value: value,
      onChange: handleSelect, disabled: disabled || loading
    },
      React.createElement('option', { value: '' }, loading ? 'Loading\u2026' : '\u2014 select an image \u2014'),
      images.map(function(img) {
        return React.createElement('option', { key: img.path, value: img.path }, img.display);
      })
    ),
    value && React.createElement('div', {
      style: { marginTop: '4px', fontSize: '11px', color: '#777', wordBreak: 'break-all' }
    }, value),
    React.createElement('div', { style: { marginTop: '8px' } },
      React.createElement('label', {
        className: 'btn btn-default btn-sm',
        style: { cursor: (uploading || disabled) ? 'not-allowed' : 'pointer', marginBottom: 0 }
      },
        React.createElement('span', { className: 'glyphicon glyphicon-upload', style: { marginRight: '5px' } }),
        uploading ? 'Uploading\u2026' : 'Upload new image\u2026',
        React.createElement('input', {
          type: 'file', accept: 'image/png,image/jpeg,image/gif,image/bmp,image/tiff,image/webp',
          style: { display: 'none' }, onChange: handleUpload, disabled: uploading || disabled
        })
      ),
      React.createElement('button', {
        type: 'button', className: 'btn btn-default btn-sm',
        style: { marginLeft: '6px' }, onClick: loadImageList, disabled: loading
      },
        React.createElement('span', { className: 'glyphicon glyphicon-refresh' })
      )
    ),
    errorMsg && React.createElement('div', {
      className: 'text-danger', style: { fontSize: '12px', marginTop: '4px' }
    }, errorMsg)
  );
});"""

    @staticmethod
    def get_definition():
        definition = get_base_definition()

        definition['id'] = ImageFileElement.element_key()
        definition['defaultProperties'].insert(len(definition['defaultProperties'])-1, "file")
        definition['required'].append("file")
        definition['properties']['type']["enum"] = [ImageFileElement.element_key()]
        definition['properties']['file'] = {
                    "type": "string",
                    "title": "File Path",
                    "description": "Absolute path (or path relative to /appconfig) of the image file to include."
                }

        return {
            ImageFileElement.element_key(): definition
        }
