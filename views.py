import os
import json
import datetime
import StringIO
from PIL import Image

import webapp2
from webapp2_extras import jinja2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files
from google.appengine.api import images

TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3


class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)


class MainHandler(BaseHandler):
    def get(self):
        context = {
            'upload': blobstore.create_upload_url('/upload'),
            }
        self.render_response('index.html', **context)


class FlavorGenericResponsive(object):
    def _add_image(self, part):
        file_name = "".join([word.lower()[0] for word in part.split("_")]) + ".png"
        self.__dict__[part] = open(os.path.join(self.base_path, file_name), "rb")

    def __init__(self, source):
        self.source = source
        self.base_path = os.path.join(os.path.split(__file__)[0], 'base/%s/' % self.flavor)

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


class FlavorGenericFixed(object):
    def __init__(self, source):
        self.source = source
        base_path = os.path.join(os.path.split(__file__)[0], 'base/%s/' % self.flavor)
        self.back = open(os.path.join(base_path, 'back.png'), "rb")
        self.reflection = open(os.path.join(base_path, 'reflection.png'), "rb")

    def mergeImages(self, image_list):
        result = Image.open(image_list[0][0])

        for image in image_list[1:]:
            if isinstance(image[0], Image.Image):
                result.paste(image[0], (image[1], image[2]), image[0])
            else:
                tmp = Image.open(image[0])
                result.paste(tmp, (image[1], image[2]), tmp)

        return result

    def renderImage(self):
        img = self.mergeImages([
            (self.back, 0, 0),
            (Image.open(self.source).resize((self.width, self.height)).convert("RGBA"), self.offset_x, self.offset_y),
            (self.reflection, 0, 0),
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
    flavor = "safari"
    margin = (93, 50, 50, 36)
    span = (93, 385, 50, 477)


class FlavorNexusOne(FlavorGenericFixed):
    width = 480
    height = 760
    offset_x = 67
    offset_y = 171
    flavor = "nexusone"


class FlavorIpad2(FlavorGenericFixed):
    width = 1018
    height = 1358
    offset_x = 139
    offset_y = 154
    flavor = "ipad2"


class MakeScreenshot(blobstore_handlers.BlobstoreUploadHandler):
    flavors = {
        "nexusone": FlavorNexusOne,
        "ipad2": FlavorIpad2,
        "safari": FlavorSafari,
    }

    def post(self):
        upload_files = self.get_uploads('screenshot')
        blob_info = upload_files[0]
        flavor = self.request.POST["flavor"]
        source = StringIO.StringIO(blobstore.BlobReader(blob_info).read())
        image = self.flavors[flavor](source)
        blob_info.delete()
        img = image.renderImage()

        result = {
            "timestamp": datetime.datetime.today().isoformat(),
            "original": str(images.get_serving_url(img, 0)),
            "preview": str(images.get_serving_url(img)),
            'upload': blobstore.create_upload_url('/upload'),
        }

        self.response.out.write(json.dumps(result))
        #self.redirect()
        #self.response.headers['Content-Type'] = 'image/png'
        #self.send_blob(img)
        #self.response.out.write()
