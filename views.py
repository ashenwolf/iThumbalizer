import json
import datetime
import StringIO

import webapp2
from webapp2_extras import jinja2

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

from base import flavors

############################################
################# Handlers #################
############################################


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
            "flavors": flavors,
            'upload': blobstore.create_upload_url('/upload'),
            }
        self.render_response('index.html', **context)


class MakeScreenshot(blobstore_handlers.BlobstoreUploadHandler):
    def _find_flavor(self, flavor):
        for f in flavors:
            if flavor == f.get_flavor_path():
                return f
        return None

    def post(self):
        upload_files = self.get_uploads('screenshot')
        blob_info = upload_files[0]
        flavor = self.request.POST["flavor"]
        fit = self.request.POST["fit"]
        source = StringIO.StringIO(blobstore.BlobReader(blob_info).read())
        image = self._find_flavor(flavor)(source, fit)
        blob_info.delete()
        img = image.renderImage()

        result = {
            "timestamp": datetime.datetime.today().isoformat(),
            "original": str(images.get_serving_url(img, 0)),
            "preview": str(images.get_serving_url(img)),
            'upload': blobstore.create_upload_url('/upload'),
        }

        self.response.out.write(json.dumps(result))


class AboutHandler(BaseHandler):
    def get(self):
        self.render_response('about.html')
