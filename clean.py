import datetime, time
import webapp2
from google.appengine.ext.blobstore import BlobInfo

LIMIT_HOURS = 1

class CleanBlobstore(webapp2.RequestHandler):
    def get(self):
        ct = datetime.datetime.fromtimestamp(time.time() - long(datetime.timedelta(hours = LIMIT_HOURS).total_seconds()))
        blobs = BlobInfo.all().filter("creation <", ct)
        for blob in blobs:
            blob.delete()
        self.response.out.write("done")

app = webapp2.WSGIApplication([
	('/clean?', CleanBlobstore),
	], debug=True)
