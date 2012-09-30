import os
from PIL import Image
from google.appengine.api import files

############################################
################ Constants #################
############################################

TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3

############################################
################# Flavors ##################
############################################


class FlavorGenericBase(object):
    @property
    def flavor_path(self):
        return self.flavor.replace(" ", "").lower()

    @classmethod
    def get_flavor_path(cls):
        return cls.flavor.replace(" ", "").lower()


class FlavorGenericResponsive(FlavorGenericBase):
    def _add_image(self, part):
        file_name = "".join([w.lower()[0] for w in part.split("_")]) + ".png"
        self.__dict__[part] = open(os.path.join(self.path, file_name), "rb")

    def __init__(self, source, fit=None):
        self.source = source
        self.path = os.path.join(os.path.split(__file__)[0], self.flavor_path)

        self._add_image("top_left")
        self._add_image("top_span")
        self._add_image("top_right")
        self._add_image("left_span")
        self._add_image("right_span")
        self._add_image("bottom_left")
        self._add_image("bottom_span")
        self._add_image("bottom_right")

    def mergeImages(self, image_list, width, height):
        result = Image.new("RGBA", (width, height))

        for image in image_list:
            if isinstance(image[0], Image.Image):
                working = image[0]
            else:
                working = Image.open(image[0])

            image_size = list(working.size)
            if image[3] >= 0:
                image_size[0] = image[3]
            if image[4] >= 0:
                image_size[1] = image[4]

            resized = working.resize(image_size)
            result.paste(resized, (image[1], image[2]), resized)

        return result

    def renderImage(self):
        source = Image.open(self.source).convert("RGBA")

        image_width = max(self.span[LEFT] + self.span[RIGHT],  source.size[0] + self.margin[LEFT] + self.margin[RIGHT])
        image_height = max(self.span[TOP] + self.span[BOTTOM], source.size[1] + self.margin[TOP] + self.margin[BOTTOM])

        span_width = image_width - (self.span[LEFT] + self.span[RIGHT])

        img = self.mergeImages([
            (self.top_left, 0, 0, -1, -1),
            (self.top_span, self.span[LEFT], 0, span_width, -1),
            (self.top_right, image_width - self.span[RIGHT], 0, -1, -1),

            (self.left_span, 0, self.span[TOP], -1, image_height - (self.span[TOP] + self.span[BOTTOM])),
            (self.right_span, image_width - self.margin[RIGHT], self.margin[TOP], -1, image_height - (self.span[TOP] + self.span[BOTTOM])),

            (self.bottom_left, 0, image_height - self.span[BOTTOM], -1, -1),
            (self.bottom_span, self.span[LEFT], image_height - self.span[BOTTOM], span_width, -1),
            (self.bottom_right, image_width - self.span[RIGHT], image_height - self.span[BOTTOM], -1, -1),

            (source, self.margin[LEFT], self.margin[TOP], -1, -1),
            ],
            image_width, image_height
            )

        # Create the file
        file_name = files.blobstore.create(mime_type='application/octet-stream')

        with files.open(file_name, 'a') as f:
            img.save(f, "PNG")

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)

        # Get the file's blob key
        blob_key = files.blobstore.get_blob_key(file_name)

        return blob_key


class FlavorGenericFixed(FlavorGenericBase):
    def __init__(self, source, fit=None):
        self.source = source
        if fit in ["all", "crop", "width", "height"]:
            self.fit = fit
        else:
            self.fit = None

        base_path = os.path.join(os.path.split(__file__)[0], self.flavor_path)
        self.back = open(os.path.join(base_path, 'back.png'), "rb")
        self.reflection = open(os.path.join(base_path, 'reflection.png'), "rb")

    def mergeImages(self, image_list):
        result = Image.open(image_list[0][0])

        for image in image_list[1:]:
            if isinstance(image[0], Image.Image):
                result.paste(
                    image[0].convert("RGB"),
                    (image[1], image[2]),
                    image[0])
            else:
                tmp = Image.open(image[0])
                result.paste(
                    tmp.convert("RGB"),
                    (image[1], image[2]),
                    tmp)

        return result

    def fitImage(self):
        image = Image.open(self.source)
        x, y = 0, 0

        if self.fit == "all":
            k = min(
                float(self.width) / image.size[0],
                float(self.height) / image.size[1])
        elif self.fit == "crop":
            k = max(
                float(self.width) / image.size[0],
                float(self.height) / image.size[1])
            x = (long(image.size[0] * k) - self.width) / 2
            y = (long(image.size[1] * k) - self.height) / 2
        elif self.fit == "width":
            k = float(self.width) / image.size[0]
        elif self.fit == "height":
            k = float(self.height) / image.size[1]
        else:
            return image.resize((self.width, self.height), Image.BICUBIC)

        i1 = image.resize(
            (long(image.size[0] * k), long(image.size[1] * k)),
            Image.BICUBIC)
        i2 = i1.crop((x, y, self.width + x, self.height + y))
        return i2

    def renderImage(self):
        img = self.mergeImages([
            (self.back, 0, 0, True),
            (self.fitImage().convert("RGBA"), self.offset_x, self.offset_y, False),
            (self.reflection, 0, 0, True),
            ])

        # Create the file
        file_name = files.blobstore.create(mime_type='application/octet-stream')

        with files.open(file_name, 'a') as f:
            img.save(f, "PNG")

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)

        # Get the file's blob key
        blob_key = files.blobstore.get_blob_key(file_name)

        return blob_key


class FlavorSafari(FlavorGenericResponsive):
    flavor = "Safari"
    margin = (94, 52, 50, 36)
    span = (94, 390, 50, 477)
    no_options = True


class FlavorNexusOne(FlavorGenericFixed):
    flavor = "Nexus One"

    width = 380
    height = 625
    offset_x = 36
    offset_y = 102
    variants = None
    orientations = None


class FlavorIpad2(FlavorGenericFixed):
    flavor = "iPad 2"

    width = 768
    height = 1002  # 1024
    offset_x = 105
    offset_y = 134
    variants = ["White", "Black"]
    orientations = ["Portrait", "Landscape"]


class FlavorIpad2White(FlavorGenericFixed):
    flavor = "iPad 2 White"

    width = 768
    height = 1002  # 1024
    offset_x = 105
    offset_y = 134
    variants = ["White", "Black"]
    orientations = ["Portrait", "Landscape"]


class FlavorIphone4(FlavorGenericFixed):
    flavor = "iPhone 4"

    width = 680
    height = 960
    offset_x = 44
    offset_y = 224
    variants = None
    orientations = None


flavors = [
    FlavorIpad2,
    FlavorIpad2White,
    FlavorIphone4,
    FlavorNexusOne,
    FlavorSafari,
    ]
