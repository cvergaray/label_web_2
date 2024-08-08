def element_image_base(image_to_add, element, im, margins, dimensions, **kwargs):
    try:
        position = element.get('position', None)

        width = element.get('width', None)
        height = element.get('height', None)
        maintainAR = element.get('maintainAR', True)

        if position is not None and len(position) == 4:
            print("4 corners specified, resizing to fit.")
            width = position[2] - position[0]
            height = position[3] - position[1]
            if maintainAR:
                width, height = constrain_width_height(image_to_add, width, height)
        else:
            if width is not None and height is None:
                # "Width specified, but no height."
                if maintainAR:
                    scale = width / image_to_add.width
                    height = int(image_to_add.height * scale)
                    # Maintaining AR, resizing to fit.
                else:
                    height = image_to_add.height
                    # Changing width only.
            elif height is not None and width is None:
                # height specified, but no width.
                if maintainAR:
                    scale = height / image_to_add.height
                    width = int(image_to_add.width * scale)
                    # Maintaining AR, resizing to fit
                else:
                    width = image_to_add.width
                    # Changing height only.

        print('[Width, Height]', width, height)

        if width is not None and height is not None:
            image_to_add = image_to_add.resize((width, height))

        print('Image to add ' + str(image_to_add))
        im.paste(image_to_add, position)
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)

    return im


def constrain_width_height(im, width, height):
    height_scale = height / im.height
    width_scale = width / im.width
    if height_scale == width_scale:
        return width, height
    proposed_width = height_scale * im.width
    proposed_height = width_scale * im.height

    height_fits = proposed_height < height
    width_fits = proposed_width < width

    if height_fits and width_fits:
        if width_scale > height_scale:
            return width, proposed_height
        else:
            return proposed_width, height
    elif width_fits:
        return proposed_width, height
    elif height_fits:
        return width, proposed_height
    else:
        return width, height
