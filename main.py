#!/usr/bin/env python
# This Python file uses the following encoding: utf-8
# vim: set autoindent:
#
#    drawtools sync server
#    Copyright (C) 2014 Viljo Viitanen
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import webapp2
import json
import time
import logging
import os

from google.appengine.api import users
from google.appengine.ext import ndb

import pprint

class Drawing(ndb.Model):
  name = ndb.StringProperty()
  owner = ndb.StringProperty()
  users = ndb.StringProperty(repeated=True)
  content = ndb.TextProperty()
  #XXX stamp is eventually used to remove old inactive entries
  stamp = ndb.DateTimeProperty(auto_now=True)


def debug(self,s):
  if self.app.debug:
    logging.debug(s)

class RootHandler(webapp2.RequestHandler):
  def get(self):

    self.response.headers['Content-Type'] = 'text/html'   
    user = users.get_current_user()
    self.response.write("""You are now logged in as %s.
<p>Enter <input value="%s" readonly> as the sync server.
<p><a href="%s">Sign out</a>""" %
      (user.nickname(),self.request.path_url, users.create_logout_url('http://www.google.com/')))

class ListHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'   
    user = users.get_current_user()
    mydrawings=Drawing.query(Drawing.owner==user.nickname()).fetch()
    debug(self,"my")
    debug(self,pprint.pprint(mydrawings))
    #XXX XXX XXX XXX XXX XXX
    for dr in mydrawings:
      self.response.write(dr.key.id())
      self.response.write("\n")
      
    otherdrawings=Drawing.query(Drawing.users==user.nickname())
    debug(self,"others")
    debug(self,pprint.pprint(otherdrawings))
    for d in otherdrawings:
      self.response.write(d.key.id())
      self.response.write("\n")

class LoadHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    key=ndb.Key('Drawing', int(self.request.GET['key']))
    obj=key.get()
    if not obj:
      self.response.write('{"error":"not found"}')
    else:
      if user.nickname()==obj.owner or user.nickname() in obj.users:
        self.response.write('{"content":%s}'%obj.content)
      else:
        self.response.write('{"error":"no access"}')
        

class SyncHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    try:
      newname=self.request.GET['name']
    except KeyError:
      newname=''
    try:
      newusers=json.loads(self.request.GET['users'])
    except KeyError:
      newusers=[]
    newcontent=self.request.GET['content']

    k=self.request.GET['key']
    if k=="new":
      obj=Drawing(name=newname,owner=user.nickname(),users=newusers,content=newcontent)
      key=obj.put()
      self.response.write('{"content":%s,"key":"%s"}'%(obj.content,obj.key))
    else:
      key=ndb.Key('Drawing', int(k))
      obj=key.get()
      if not obj:
        self.response.write('{"error":"not found"}')
      if user.nickname()==obj.owner or user.nickname() in obj.users:
        self.response.write('{"content":%s}'%obj.content)
	return
      else:
        self.response.write('{"error":"no access"}')
	return
      obj.content=newcontent
      obj.users=newusers
      obj.put()
      self.response.write('{"content":%s,"key":"%s"}'%(obj.content,obj.key))

debugstate = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes=[
    ('/list', ListHandler),
    ('/load', LoadHandler),
    ('/sync', SyncHandler),
    ('/', RootHandler),
], debug=debugstate)
