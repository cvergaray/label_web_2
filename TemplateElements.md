# Template File
<!-- TOC -->
* [Template File](#template-file)
  * [Rendering Elements](#rendering-elements)
    * [DataMatrix](#datamatrix)
    * [Code](#code)
    * [Text](#text)
    * [Image](#image)
  * [Non-Rendering Elements](#non-rendering-elements)
    * [Array Index](#array-index)
    * [Dictionary Item](#dictionary-item)
    * [JSON API](#json-api)
    * [JSON Payload](#json-payload)
    * [Grocy Entry API](#grocy-entry-api)
<!-- TOC -->

Label templates are JSON files or YAML files in the running directory with the extension of lbl. An example YAML file can be found at grocy-test.lbl<br/>
lbl template files may optionally include the label width and height. The main thing that the JSON object requires is a list of elements to be included on the label.

| Property Key | Example Value          | Description                                         | Required | Default Value                                                |
|--------------|------------------------|-----------------------------------------------------|----------|--------------------------------------------------------------|
| name         | grocy label            | A value to describe the label                       | false    | N/A                                                          |
| elements     | < See examples below > | A collection of the elements to render on the label | true     | N/A                                                          |
| width        | 457                    | The width of the label in pixels/dots               | false    | The width provided by Implementation.get_label_width_height  |
| height       | 254                    | The height of the label in pixels/dots              | false    | The height provided by Implementation.get_label_width_height |

```javascript
{
    "name": "Example Label with no elements",
    "elements": [] 
}
```

```yaml
name: Example Label with no elements
elements: []

```

There are two types of elements: Rendering and non-rendering elements. 
- Rendering elements will result in something getting added to the generated label.
- Non-rendering elements transform data and pass it to child elements.

## Rendering Elements

Rendering elements can include data in a few ways:
- hard-coded data in a `data` property or 
- pulled from the request sent to the API using the `key` property.
- pulled from the `data` or the data provided by `key` using the `datakey` property.

The example elements in this document include one hard-coded and one key-based element.

### DataMatrix
Datamatrix elements encode the data into a datamatrix code for use with 3D barcode scanners.

| Property Key      | Example Value             | Description                                                                                                                | Required                       | Default Value |
|-------------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------|--------------------------------|---------------|
| name              | grocycode                 | A value to describe the element                                                                                            | false                          | N/A           |
| type              | datamatrix                | indicates that this is a datamatrix element                                                                                | true                           | N/A           |
| data              | grcy:p:130:x65a70d139b122 | The hard-coded text value to be rendered or data source for `datakey`.                                                     | true IF 'key' is not included  | N/A           |
| key               | grocycode                 | The key identifying the property from the HTML request that will be set as the `data` property                             | true IF 'data' is not included | N/A           |
| datakey           | grocycode                 | The key identifying the property from the `data` to be used as the `data`                                                  | false                          | N/A           |
| size              | SquareAuto                | The desired modulesize of datamatrix element. SquareAuto or RectAuto or one defined by ENCODING_SIZE_NAMES in pylibdtmx    | false                          | SquareAuto    |
| img_size          | 100                       | The real Datamatrix size on the label 100 = 100x100 px or set both by 100x50 but get shure you set RectAuto if not square  | false                          | N/A           |
| horizontal_offset | 15                        | The number of pixels to offset the element from the left of the label.                                                     | true                           | N/A           |
| vertical_offset   | 130                       | The number of pixels to offset the element from the top of the label                                                       | true                           | N/A           |
```javascript
{
    "elements": [
        {
            "name": "hard-coded DataMatrix",
            "type": "datamatrix",
            "data": "hard-coded data to encode in datamatrix",
            "horizontal_offset": 15,
            "vertical_offset": 22
        },
        {
            "name": "grocycode pulled from request",
            "type": "datamatrix",
            "key": "grocycode",
            "horizontal_offset": 15,
            "vertical_offset": 22
        },
        {
            "name": "grocycode pulled from data using a key value",
            "type": "datamatrix",
            "data": { "grocycode": "grcy:p:123" },
            "datakey": "grocycode",
            "horizontal_offset": 15,
            "vertical_offset": 22
        }
    ]
}
```
```yaml
elements:
  - name: hard-coded DataMatrix
    type: datamatrix
    data: hard-coded data to encode in datamatrix
    horizontal_offset: 15
    vertical_offset: 22
  - name: grocycode pulled from request
    type: datamatrix
    key: grocycode
    horizontal_offset: 15
    vertical_offset: 22
  - name: grocycode pulled from data using a key value
    type: datamatrix
    data:
      grocycode: grcy:p:123
    datakey: grocycode
    horizontal_offset: 15
    vertical_offset: 22
```
### Code
Code Element to create 2D and 3D Codes like code39, code128, qrcode etc.

| Property Key      | Example Value             | Description                                                                                                                | Required                       | Default Value |
|-------------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------|--------------------------------|---------------|
| name              | code1                     | A value to describe the element                                                                                            | false                          | N/A           |
| type              | qrcode                    | The codetype to be created                                                                                                 | true                           | N/A           |
| data              | "ABC12345"                | The data of the code element                                                                                               | true                           | N/A           |
| img_size          | 200x200                   | The real Code size on the label 100 = 100x100 px or set both by 100x50                                                     | false                          | N/A           |
| horizontal_offset | 15                        | The number of pixels to offset the element from the left of the label.                                                     | true                           | N/A           |
| vertical_offset   | 130                       | The number of pixels to offset the element from the top of the label                                                       | true                           | N/A           |

```javascript
{
    "elements": [
        {
            "name": "code1",
            "type": "qrcode",
            "data": "ABC12345",
            "img_size": "200x200",
            "horizontal_offset": 15,
            "vertical_offset": 22
        }
    ]
}
```
```yaml
elements:
  - name: code1
    type: qrcode
    data: "ABC12345"
    img_size: 200x200
    horizontal_offset: 15
    vertical_offset: 22
```
### Text

Text elements render raw text. In addition to being useful for printing data provided in the request, when using a hardcoded value, this could be used as a label.

| Property Key      | Example Value | Description                                                                                                                   | Required                       | Default Value |
|-------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------|--------------------------------|---------------|
| name              | duedate       | A value to describe the element                                                                                               | false                          | N/A           |
| type              | text          | indicates that this is a text element                                                                                         | true                           | N/A           |
| data              | 2024-02-29    | The hard-coded text value to be rendered.                                                                                     | true IF 'key' is not included  | N/A           |
| key               | duedate       | The key identifying the property from the HTML request that will be rendered                                                  | true IF 'data' is not included | N/A           |
| datakey           | note          | The key identifying the property from the `data` to be used as the `data`                                                     | false                          | N/A           |
| shrink            | true          | When true, the font size will automatically shrink to fit                                                                     | false                          | false         |
| wrap              | 70            | The number of characters that is allowed on a single line. When set, text will wrap onto a new line if longer than this value | false                          | None          |
| font_size         | 24            | The size of the font to be rendered. When not provided, it will pull from the HTML request, if available.                     | false                          | 40            |
| fill_color        | (255,0,0)     | A tuple of (R,G,B) values indicating the color of the text. Only applicable for multicolor printers                           | false                          | (0,0,0)       |
| horizontal_offset | 15            | The number of pixels to offset the element from the left of the label.                                                        | true                           | N/A           |
| vertical_offset   | 130           | The number of pixels to offset the element from the top of the label                                                          | true                           | N/A           |

```javascript
{
    "elements": [
        {
            "name": "hard-coded duedate",
            "type": "text",
            "data": "2024-02-29",
            "shrink": true,
            "wrap": 24,
            "horizontal_offset": 130,
            "vertical_offset": 50
        },
        {
            "name": "product pulled from request",
            "type": "text",
            "key": "product",
            "shrink": true,
            "wrap": 24,
            "horizontal_offset": 15,
            "vertical_offset": 130
        },
        {
            "name": "product pulled from request",
            "type": "text",
            "data" : {"id": 1, "note": "This is the property I care about."},
            "datakey": "note",
            "shrink": true,
            "wrap": 24,
            "horizontal_offset": 15,
            "vertical_offset": 130
        }
    ]
}
```
```yaml
elements:
  - name: hard-coded duedate
    type: text
    data: '2024-02-29'
    shrink: true
    wrap: 24
    horizontal_offset: 130
    vertical_offset: 50
  - name: product pulled from request
    type: text
    key: product
    shrink: true
    wrap: 24
    horizontal_offset: 15
    vertical_offset: 130
  - name: product pulled from request
    type: text
    data:
      id: 1
      note: This is the property I care about.
    datakey: note
    shrink: true
    wrap: 24
    horizontal_offset: 15
    vertical_offset: 130

```

### Image

Image elements render Images either from a local file or downloaded from a URL.

| Property Key | Example Value                                       | Description                                                                                                                                     | Required                                                                              | Default Value |
|--------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------|
| name         | duedate                                             | A value to describe the element                                                                                                                 | false                                                                                 | N/A           |
| type         | image_file                                          | indicates that this is an image element. Should be either image_file or image_url                                                               | true                                                                                  | N/A           |
| file         | my_image.png                                        | The path of the image to be rendered.                                                                                                           | true IF 'type' is image_file                                                          | N/A           |
| url          | https://avatars.githubusercontent.com/u/8941602?v=4 | The web url to the image to be rendered.                                                                                                        | true IF 'type' is image_url                                                           | N/A           |
| position     | [35, 35, 335, 335]                                  | The position of the image as either one or two sets of coordinate points indicating the pixel offset for the top left and bottom right corners. | true (only 2 numbers if width and height are set or no resizing desired, 4 otherwise) | N/A           |
| width        | 120                                                 | The width of the image. When maintainAR is set, this is the maximum width.                                                                      | false                                                                                 | N/A           |
| height       | 120                                                 | The height of the image. When maintainAR is set, this is the maximum height.                                                                    | false                                                                                 | false         |
| maintainAR   | true                                                | Indicates that when resizing the image the Aspect Ratio will be maintained.                                                                     | true                                                                                  | None          |

```javascript
{
    "elements": [
        {
            "name": "LinkTree",
            "type": "image_file",
            "file": "/appconfig/linktree.png",
			"position": [35, 35, 335, 335]
        },
        {
            "name": "Logo",
            "type": "image_url",
            "url": "https://avatars.githubusercontent.com/u/8941602?v=4",
			"position": [335, 35],
            "width": 300,
            "height": 300,
            "maintainAR": true
        },
        {
            "name": "Business Name",
            "type": "text",
            "data": "My Great Business",
            "shrink": true,
            "wrap": 24,
			"font_size": 150,
            "horizontal_offset": 350,
            "vertical_offset": 100
        }
    ]
}
```

```yaml
elements:
  - name: LinkTree
    type: image_file
    file: /appconfig/linktree.png
    position:
      - 35
      - 35
      - 335
      - 335
  - name: Logo
    type: image_url
    url: https://avatars.githubusercontent.com/u/8941602?v=4
    position:
      - 335
      - 35
    width: 300
    height: 300
    maintainAR: true
  - name: Business Name
    type: text
    data: My Great Business
    shrink: true
    wrap: 24
    font_size: 150
    horizontal_offset: 350
    vertical_offset: 100

```
## Non-Rendering Elements

### Array Index

Retrieves the item from the data property at the specified index and sets the `data` property of the child elements to that item.

| Property Key | Example Value                   | Description                                          | Required                               | Default Value |
|--------------|---------------------------------|------------------------------------------------------|----------------------------------------|---------------|
| name         | Indexed Item                    | A value to describe the element                      | false                                  | N/A           |
| data         | ["Sunday", "Monday", "Tuesday"] | The list of items to index                           | true if not provided by parent element | 0             |
| type         | data_array_index                | indicates that this is a data array index element    | true                                   | N/A           |
| index        | 1                               | The index of the item to be passed to child elements | true                                   | N/A           |
| elements     | < SEE OTHER ELEMENTS >          | A collection of the elements to render on the label. | false                                  | N/A           |

```javascript
{
    "elements": [
        {
            "data": ["Sunday", "Monday", "Tuesday"],
            "index": 1,
            "type": "data_array_index",
            "elements": [
                {
                    "horizontal_offset": 130,
                    "name": "Monday",
                    "shrink": true,
                    "type": "text",
                    "vertical_offset": 70,
                    "wrap": 24
                }
            ]
        }
    ]
}
```

```yaml
elements:
  - data:
      - Sunday
      - Monday
      - Tuesday
    index: 1
    type: data_array_index
    elements:
      - horizontal_offset: 130
        name: Monday
        shrink: true
        type: text
        vertical_offset: 70
        wrap: 24

```

### Dictionary Item

Retrieves the item from the data property with the given `key` and sets the `data` property of the child elements to that item.

| Property Key | Example Value                                                     | Description                                          | Required                               | Default Value |
|--------------|-------------------------------------------------------------------|------------------------------------------------------|----------------------------------------|---------------|
| name         | Dictionary Item                                                   | A value to describe the element                      | false                                  | N/A           |
| data         | {"userId": 1, "title": "delectus aut autem", "completed": false } | The dictionary to index                              | true if not provided by parent element | 0             |
| type         | data_dict_item                                                    | indicates that this is a data dict item element      | true                                   | N/A           |
| key          | title                                                             | The key of the item to be passed to child elements   | true                                   | N/A           |
| elements     | < SEE OTHER ELEMENTS >                                            | A collection of the elements to render on the label. | false                                  | N/A           |

```javascript
{
    "elements": [
        {
            "key": "title",
            "type": "data_dict_item",
            "data": {
                    "userId": 1,
                    "id": 1,
                    "title": "delectus aut autem",
                    "completed": false
                },
            "elements": [
                {
                    "horizontal_offset": 130,
                    "name": "Title passed from parent element",
                    "shrink": true,
                    "type": "text",
                    "vertical_offset": 70,
                    "wrap": 24
                }
            ]
        }
    ]
}
```
```yaml
elements:
  - key: title
    type: data_dict_item
    data:
      userId: 1
      id: 1
      title: delectus aut autem
      completed: false
    elements:
      - horizontal_offset: 130
        name: Title passed from parent element
        shrink: true
        type: text
        vertical_offset: 70
        wrap: 24

```

### JSON API

JSON API elements will query a web API for a JSON object and then assign that object to the `data` property of children elements.
This means that anything provided in the `data` property of the child elements will be ignored and replaced with the API response.

| Property Key | Example Value                                | Description                                                                                           | Required                    | Default Value                                                             |
|--------------|----------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------|---------------------------------------------------------------------------|
| name         | API                                          | A value to describe the element                                                                       | false                       | N/A                                                                       |
| endpoint     | https://jsonplaceholder.typicode.com/todos/1 | The URL of the API to be called                                                                       | true                        | N/A                                                                       |
| type         | json_api                                     | indicates that this is a json_api element                                                             | true                        | N/A                                                                       |
| data         | {"id": "grcy:p:123"}                         | Hard coded values to be provided in the data of the request.                                          | false                       | N/A                                                                       |
| datakey      | id                                           | The key identifying the property from the HTML request that will be passed in the data of the request | false                       | N/A                                                                       |
| datakeyname  | grocycode                                    | The key for the data retrieved with datakey when sent to the request.                                 | true IF datakey is provided | N/A                                                                       |
| headers      | {"API_KEY": "ABC123"}                        | A dictionary of header values to be sent with the request.                                            | false                       | None. But {'accept': 'application/json'} will always be added by default. |
| method       | get                                          | The HTTP method used when querying the API. Must be one of ['get', 'post', 'put', 'delete']           | false                       | get                                                                       |
| elements     | < SEE OTHER ELEMENTS >                       | A collection of the elements to render on the label.                                                  | false                       | N/A                                                                       |

```javascript
{
    "elements": [
        {
            "name": "hard-coded duedate",
            "type": "json_api",
            "endpoint": "https://jsonplaceholder.typicode.com/todos/1",
            "elements": [
                {
                    "name": "Title pulled from API Response",
                    "type": "text",
                    "datakey": "title",
                    "shrink": true,
                    "wrap": 24,
                    "horizontal_offset": 15,
                    "vertical_offset": 130
                },
                {
                    "name": "Completion Status pulled from API Response",
                    "type": "text",
                    "datakey": "completed",
                    "shrink": true,
                    "wrap": 24,
                    "horizontal_offset": 15,
                    "vertical_offset": 30
                }
            ]
        }
    ]
}
```
```yaml
elements:
  - name: hard-coded duedate
    type: json_api
    endpoint: https://jsonplaceholder.typicode.com/todos/1
    elements:
      - name: Title pulled from API Response
        type: text
        datakey: title
        shrink: true
        wrap: 24
        horizontal_offset: 15
        vertical_offset: 130
      - name: Completion Status pulled from API Response
        type: text
        datakey: completed
        shrink: true
        wrap: 24
        horizontal_offset: 15
        vertical_offset: 30

```

### JSON Payload

JSON Payload elements will pull data from JSON submitted with the web request calling for the label to be rendered and then assign requested object to the `data` property of children elements. If no key is provided, the entire JSON payload is provided to children elements.
This means that anything provided in the `data` property of the child elements will be ignored and replaced with the retrieved value.

| Property Key | Example Value                                | Description                                                                                            | Required | Default Value |
|--------------|----------------------------------------------|--------------------------------------------------------------------------------------------------------|----------|---------------|
| name         | API                                          | A value to describe the element                                                                        | false    | N/A           |
| type         | from_json_payload                            | indicates that this is a json_api element                                                              | true     | N/A           |
| key          | id                                           | The key identifying the property from the JSON payload that will be passed in the data of the request. | false    | N/A           |
| elements     | < SEE OTHER ELEMENTS >                       | A collection of the elements to render on the label.                                                   | false    | N/A           |

```javascript
{
    "elements": [
        {
            "name": "hard-coded duedate",
            "type": "from_json_payload",
            "elements": [
                {
                    "name": "Title pulled from JSON Payload",
                    "type": "text",
                    "datakey": "title",
                    "shrink": true,
                    "wrap": 24,
                    "horizontal_offset": 15,
                    "vertical_offset": 130
                },
                {
                    "name": "Completion Status pulled from JSON Payload",
                    "type": "text",
                    "datakey": "completed",
                    "shrink": true,
                    "wrap": 24,
                    "horizontal_offset": 15,
                    "vertical_offset": 30
                }
            ]
        }
    ]
}
```
```yaml
elements:
  - name: hard-coded duedate
    type: from_json_payload
    elements:
      - name: Title pulled from JSON Payload
        type: text
        datakey: title
        shrink: true
        wrap: 24
        horizontal_offset: 15
        vertical_offset: 130
      - name: Completion Status pulled from JSON Payload
        type: text
        datakey: completed
        shrink: true
        wrap: 24
        horizontal_offset: 15
        vertical_offset: 30

```

### Grocy Entry API

The Grocy Entry API element is a convenience wrapper around the JSON API element that makes it easier to get details 
about a grocy entry. However, not all properties of the JSON API apply. Only the properties listed here are valid.

**NOTE: The HTTP request that triggers this label must include a grocycode property**

| Property Key | Example Value                   | Description                                                                                                                     | Required                    | Default Value                                                                                           |
|--------------|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------|
| name         | Grocy API                       | A value to describe the element                                                                                                 | false                       | N/A                                                                                                     |
| endpoint     | http://grocy.local:9283         | The URL of the grocy server                                                                                                     | true                        | N/A                                                                                                     |
| type         | grocy_entry                     | indicates that this is a grocy entry element                                                                                    | true                        | N/A                                                                                                     |
| grocycode    | grcy:p:123:x64c4502d1694e       | Hardcoded grocycode to be used for the request. If omitted, the http request for printing the label must include this property. | false                       | N/A                                                                                                     |
| api_key      | <YOUR GROCY API KEY>            | The Grocy API key generated by your grocy instance.                                                                             | true                        | N/A                                                                                                     |
| datakeyname  | grocycode                       | The key for the data retrieved with datakey when sent to the request.                                                           | true IF datakey is provided | N/A                                                                                                     |
| headers      | {"ADDITIONAL_HEADER": "ABC123"} | A dictionary of header values to be sent with the request.                                                                      | false                       | {'accept': 'application/json', 'GROCY-API-KEY': <YOUR GROCY API KEY> } will always be added by default. |
| method       | get                             | The HTTP method used when querying the API. Must be one of ['get', 'post', 'put', 'delete']                                     | false                       | get                                                                                                     |
| elements     | < SEE OTHER ELEMENTS >          | A collection of the elements to render on the label.                                                                            | false                       | N/A                                                                                                     |

```javascript
{
    "elements": [
        {
            "api_key": "YOUR_API_KEY_HERE",
            "name": "GROCY ProductAPI",
            "endpoint": "http://YOUR_IP_HERE:9283",
            "type": "grocy_entry",
            "elements": [
                {
                    "name": "Translation element because the Grocy API returns an array of items",
                    "index": 0,
                    "type": "data_array_index",
                    "elements": [
                        {
                            "horizontal_offset": 130,
                            "name": "Note",
                            "key": "note",
                            "shrink": true,
                            "type": "text",
                            "vertical_offset": 70,
                            "wrap": 24
                        }
                    ]
                }
            ]
        }
    ]
}
```
```yaml
elements:
  - api_key: YOUR_API_KEY_HERE
    name: GROCY ProductAPI
    endpoint: http://YOUR_IP_HERE:9283
    type: grocy_entry
    elements:
      - name: Translation element because the Grocy API returns an array of items
        index: 0
        type: data_array_index
        elements:
          - horizontal_offset: 130
            name: Note
            key: note
            shrink: true
            type: text
            vertical_offset: 70
            wrap: 24

```
