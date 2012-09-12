#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os.path

from views import MainHandler, MakeNexusOne

class NullUndefined(jinja2.Undefined):
    def __int__(self):
        return ''
    def __float__(self):
        return ''
    def __getattr__(self, name):
        return ''

config = {
#    'webapp2_extras.i18n': {
#        'translations_path': os.path.join(os.path.dirname(__file__), 'locale'),
#        },
    'webapp2_extras.jinja2' : {
        'environment_args': {
            'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.with_'], #'jinja2.ext.i18n', 
            'undefined': NullUndefined,
            },
#        'filters': {
#            'serve_image': misc.filters.serve_image,
#            'upload_url': misc.filters.upload_url,
#            'htmlify': misc.filters.htmlify,
#            'datetime': misc.filters.format_datetime,
#            },
#	    'globals': {
#            'url': webapp2.uri_for,
#            'settings': skolladmin.models.SiteSettings,
#	        },
        },
    'template_path': os.path.join(os.path.dirname(__file__), 'templates/'),
    }   

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/nexusone', MakeNexusOne),
	], debug=True, config=config)
