def element_image_base(image_to_add, element, im, margins, dimensions, **kwargs):
    try:
        image_to_add = image_to_add.convert('RGB')

        position = element.get('position', None)

        width = element.get('width', None)
        height = element.get('height', None)
        maintain_ar = element.get('maintainAR', True)

        if position is not None and len(position) == 4:
            width = position[2] - position[0]
            height = position[3] - position[1]
            if maintain_ar:
                width, height = constrain_width_height(image_to_add, width, height)
                position[2] = position[0] + width
                position[3] = position[1] + height
        else:
            if width is not None and height is None:
                # "Width specified, but no height."
                if maintain_ar:
                    scale = width / image_to_add.width
                    height = int(image_to_add.height * scale)
                    # Maintaining AR, resizing to fit.
                else:
                    height = image_to_add.height
                    # Changing width only.
            elif height is not None and width is None:
                # height specified, but no width.
                if maintain_ar:
                    scale = height / image_to_add.height
                    width = int(image_to_add.width * scale)
                    # Maintaining AR, resizing to fit
                else:
                    width = image_to_add.width
                    # Changing height only.

        if width is not None and height is not None:
            image_to_add = image_to_add.resize((int(width), int(height)))

        im.paste(image_to_add, position)
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)

    return im


def constrain_width_height(im, width, height):
    height_scale = height / im.height
    width_scale = width / im.width
    if height_scale == width_scale:
        return width, height
    proposed_width = int(height_scale * im.width)
    proposed_height = int(width_scale * im.height)

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
