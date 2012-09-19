import os
import StringIO
from PIL import Image

import webapp2
from webapp2_extras import jinja2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from google.appengine.api import images

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
            'upload': {
                'nexusone': blobstore.create_upload_url('/nexusone'),
                },
            }
        self.render_response('index.html', **context)

class FlavorGenericFixed(object):
    def __init__(self, source):
        self.source = images.resize(source, self.width, self.height)

        base_path = os.path.join(os.path.split(__file__)[0], 'base/%s/' % self.flavor)
        self.back = open(os.path.join(base_path, 'back.png'), "rb").read()
        self.reflection = open(os.path.join(base_path, 'reflection.png'), "rb").read()

        back = images.Image(self.back)
        self.target_width = back.width
        self.target_height = back.height

        buf = StringIO.StringIO()
        

        self.im_back = Image.open(os.path.join(base_path, 'back.png'))
        self.im_cover = Image.open(os.path.join(base_path, 'reflection.png'))
        #im_contents = Image.fromstring('RGBA', (blob_image.width, blob_image.height), blob_image)
        #src_ing = images.Image(blob_image)

    def renderImage(self):
        return images.composite(
            [
#            (self.back,         0,              0,                  1.0,    images.TOP_LEFT),
            (self.im_back,         0,              0,                  1.0,    images.TOP_LEFT),
            (self.source,       self.offset_x,  self.offset_y,      1.0,    images.TOP_LEFT),
#            (self.reflection,   0,              0,                  1.0,    images.TOP_LEFT),
            (self.im_cover,   0,              0,                  1.0,    images.TOP_LEFT),
            ],
            self.target_width,
            self.target_height
            )

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

class MakeNexusOne(blobstore_handlers.BlobstoreUploadHandler):
    flavors = {
        "nexusone": FlavorNexusOne,
        "ipad2": FlavorIpad2,
    }

    def post(self):
        upload_files = self.get_uploads('screenshot')
        blob_info = upload_files[0]
        flavor = self.request.POST["flavor"]
        image = self.flavors[flavor](blobstore.BlobReader(blob_info).read())
        blob_info.delete()

        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(image.renderImage())
