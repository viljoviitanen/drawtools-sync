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
import hashlib
import zlib
import base64

from google.appengine.api import users
from google.appengine.ext import ndb

import pprint

class Drawing(ndb.Model):
  name = ndb.StringProperty()
  owner = ndb.StringProperty()
  shared = ndb.StringProperty(repeated=True)
  sharekey = ndb.StringProperty()
  content = ndb.TextProperty()
  #XXX stamp is eventually used to remove old inactive entries
  stamp = ndb.DateTimeProperty(auto_now=True)


def debug(self,s):
  if self.app.debug:
    logging.debug(s)

class RootHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'   
    self.response.write('See the server source at <a href="https://github.com/viljoviitanen/drawtools-sync">https://github.com/viljoviitanen/drawtools-sync</a>')

class LogoutHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'   
    self.response.write("You have logged out.")

class LoginHandler(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()

    self.response.headers['Content-Type'] = 'text/html'   
    self.response.write("""You are now logged in as %s.
<p><tt>%s</tt> is the sync server.
<p><a href="%s">Sign out</a>""" %
      (user.email(),self.request.host_url, users.create_logout_url(self.request.host_url+'/logout')))

class TestHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'   
    user = users.get_current_user()
    if not user:
      self.response.write('Please <a href="/login">log in</a> first.')
      return
    email=user.email()

    self.response.write("""
<!--
The following javascript example code here is public domain.
-->
You are now logged in as %s.
<p>
<script src='//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js'></script>
<script src='zpipe.min.js'></script>
<script>
function create() {
  $('#item').html('Name: <input id=name value="New Drawing"> Content: <input id=content> Shared with: <input id=shared value="[]"><input id=key type=hidden> <button onclick="save()">Save</button> <p> Note: shared emails format is a json array: <tt>["email.address@example.com","another.address@example.com"]</tt>')
}

function del() {
  key=$('#key').val()
  name=$('#name').val()
  if (!confirm("Really delete " + escapehtml(name) + "?")) return
  $.ajax({
    dataType: "jsonp",
    url: '/delete',
    data: {'key':key},
    success: function(data) {
    if(data.error) {
       alert("Could not delete: "+data.error)
       return
    }
    if(!data.key) {
       alert("Could not delete")
       return
    }

    alert("delete successful")
    //reload...
    list()
    }
  })
}

function save() {
  key=$('#key').val()
  if (key=='') {
    key='new'
  }
  name=$('#name').val()
  content=$('#content').val()
  try {
    obj=$.parseJSON(content)
  } catch (e) {
    obj=null
  }
  if (!obj) {
    alert("content is not valid JSON")
    return
  }
  shared=$('#shared').val()
  //base64-encoded zlib-deflated data.
  c=btoa(zpipe.deflate(JSON.stringify({'key':key,'name':name,'content':content,'shared':shared})))
  //jsonp calls are GET calls and the url must not be greater than about 2k bytes.
  if(c.length > 1888) {
    alert("Sorry, too much data in the drawing!"+c.length)
    return
  }
  $.ajax({
    dataType: "jsonp",
    url: '/sync',
    data: {'c':c},
    success: function(data) {
    if(data.error) {
       alert("Could not sync data: "+data.error)
       return
    }
    if(!data.content) {
       alert("Could not sync data.")
       return
    }
    if(!data.key) {
       alert("Server did not return the key. What?!")
       return
    }

    alert("save successful")
    // save the key from the server, in case this was a new drawing!
    $('#key').val(data.key)
    }
  })
}

function loadwithkey(sharekey) {
  $.ajax({
    dataType: "jsonp",
    url: '/loadwithkey',
    data: {'sharekey':sharekey },
    success: function(data) {
    if(data.error) {
       alert("Could not load data: "+data.error)
       return
    }
    if(!data.content) {
       alert("Could not load data.")
       return
    }
    if (!data.name) data.name="(unnamed)"
    
    $('#item').html('Name: <input id=name value="'+escapehtml(data.name)+'"> Content: <input id=content> Shared with: <input id=shared><input id=key type=hidden value="'+data.key+'"> Share Key: <input id=sharekey value="'+data.sharekey+'"> <button onclick="save()">Save</button><button onclick="del()">Delete</button> <p> Note: shared emails format is a json array: <tt>["email.address@example.com","another.address@example.com"]</tt>')
    $('#content').val(JSON.stringify(data.content))
    $('#shared').val(JSON.stringify(data.shared))
    }
  })
}

function load(key) {
  $.ajax({
    dataType: "jsonp",
    url: '/load',
    data: {'key':key },
    success: function(data) {
    if(data.error) {
       alert("Could not load data: "+data.error)
       return
    }
    if(!data.content) {
       alert("Could not load data.")
       return
    }
    if (!data.name) data.name="(unnamed)"
    
    $('#item').html('Name: <input id=name value="'+escapehtml(data.name)+'"> Content: <input id=content> Shared with: <input id=shared><input id=key type=hidden value="'+data.key+'"> Share Key: <input id=sharekey value="'+data.sharekey+'"> <button onclick="save()">Save</button><button onclick="del()">Delete</button> <p> Note: shared emails format is a json array: <tt>["email.address@example.com","another.address@example.com"]</tt>')
    $('#content').val(JSON.stringify(data.content))
    $('#shared').val(JSON.stringify(data.shared))
    }
  })
}

function list() {
  $.ajax({
  dataType: "jsonp",
  url: '/list',
  success: function(data) {
    if(!data.own) {
       alert("Could not load data.")
       return
    }
    own=data.own
    shared=data.shared
    init()
  }
  })
}

function init() {
  s="My drawings:<br>"
  for (i = 0; i < own.length; i++) {
    name=own[i].name
    if (!name) name="(unnamed)"
    s+='<a href="javascript:load('+own[i].key+')">' + name + '</a><br>'
  }
  s+="Shared drawings:<br>"
  for (i = 0; i < shared.length; i++) {
    name=shared[i].name
    if (!name) name="(unnamed)"
    s+='<a href="javascript:load('+shared[i].key+')">' + name + '</a><br>'
  }
  $('#list').html(s)

}

function escapehtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

</script>
<button onclick="create()">Create new</button>
<button onclick="list()">Get List</button>
<input id="key"><button onclick="loadwithkey(document.getElementById('key').value)">Get via share key</button>
<div id=list></div>
<div id=item></div>

<!--
public domain code ends.
-->
""" % email )
def wrapwrite(self,json):
  self.response.write(self.request.GET['callback']+"("+json+")")

class ListHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/javascript'
    user = users.get_current_user()
    if not user:
      wrapwrite(self,json.dumps({'error':'not logged in at the sync server'}))
      return
    email=user.email().lower()
    mydrawings=Drawing.query(Drawing.owner==email).fetch()
    debug(self,"my")
    debug(self,pprint.pformat(mydrawings))
    own=[]
    for dr in mydrawings:
      own.append({'key':dr.key.id(),'name':dr.name})
      
    shareddrawings=Drawing.query(Drawing.shared==email)
    debug(self,"shared")
    debug(self,pprint.pformat(shareddrawings))
    shared=[]
    for dr in shareddrawings:
      shared.append({'key':dr.key.id(),'name':dr.name})
    wrapwrite(self,json.dumps({'own':own,'shared':shared}))
      

class LoadWithKeyHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/javascript'
    user = users.get_current_user()
    if not user:
      wrapwrite(self,json.dumps({'error':'not logged in at the sync server'}))
      return
    email=user.email().lower()
    sharekey=self.request.GET['sharekey'].rstrip().lower() #guard against whitespace after copypaste
    if len(sharekey) != 32:
      wrapwrite(self,json.dumps({'error':'invalid key'}))
      return
    mydrawings=Drawing.query(Drawing.sharekey==sharekey).fetch()
    if len(mydrawings) == 0:
      wrapwrite(self,json.dumps({'error':'sharing key not found'}))
      return
      
    key=ndb.Key('Drawing', mydrawings[0].key.id())
    obj=key.get()
    if not obj:
      wrapwrite(self,json.dumps({'error':'internal error'}))
    else:
      if email==obj.owner or email in obj.shared:
        pass
      else:
        obj.shared.append(email)
        key=obj.put()
      wrapwrite(self,'{"key":%s,"content":%s,"name":%s,"shared":%s,"sharekey":%s}'%(key.id(),obj.content,json.dumps(obj.name),json.dumps(obj.shared),json.dumps(obj.sharekey)))
        

class LoadHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/javascript'
    user = users.get_current_user()
    if not user:
      wrapwrite(self,json.dumps({'error':'not logged in at the sync server'}))
      return
    email=user.email().lower()
    key=ndb.Key('Drawing', int(self.request.GET['key']))
    obj=key.get()
    if not obj:
      wrapwrite(self,json.dumps({'error':'not found'}))
    else:
      if email==obj.owner or email in obj.shared:
        wrapwrite(self,'{"key":%s,"content":%s,"name":%s,"shared":%s,"sharekey":%s}'%(self.request.GET['key'],obj.content,json.dumps(obj.name),json.dumps(obj.shared),json.dumps(obj.sharekey)))
      else:
        wrapwrite(self,json.dumps({'error':'no access'}))
        

class SyncHandler(webapp2.RequestHandler):
  #cross domain issue, cannot be a post.
  def get(self):
    self.response.headers['Content-Type'] = 'application/javascript'
    user = users.get_current_user()
    if not user:
      wrapwrite(self,json.dumps({'error':'not logged in at the sync server'}))
      return
    email=user.email().lower()
    try:
      c=self.request.GET['c']
      #If c parameter does not exist, data is in legacy uncompressed format
      try:
        j=json.loads(zlib.decompress(base64.b64decode(c)))
      except zlib.error:
        wrapwrite(self,'{"error":"server got invalid compressed data"}')
        return
      except TypeError:
        wrapwrite(self,'{"error":"server probably got invalid base64 data"}')
        return
      except ValueError:
        wrapwrite(self,'{"error":"server probably got invalid json data"}')
	return
      try:
        newname=j['name']
      except KeyError:
        newname=''
      try:
        newusers=json.loads(j['shared'])
      except KeyError:
        newusers=[]
      except ValueError:
        wrapwrite(self,'{"error":"invalid shared list"}')
        return
      try:
        newcontent=j['content']
      except KeyError:
        newcontent='{}'
      try:
        k=j['key']
      except KeyError:
        wrapwrite(self,'{"error":"server did not get key"}')
        return
    #uncompressed data from older versions of the plugin
    except KeyError:
      try:
        newname=self.request.GET['name']
      except KeyError:
        newname=''
      try:
        newusers=json.loads(self.request.GET['shared'])
      except KeyError:
        newusers=[]
      except ValueError:
        wrapwrite(self,'{"error":"invalid shared list"}')
        return
      try:
        newcontent=self.request.GET['content']
      except KeyError:
        newcontent='{}'
      try:
        k=self.request.GET['key']
      except KeyError:
        wrapwrite(self,'{"error":"server did not get key"}')
        return

    debug(self,"sync")
    debug(self,pprint.pformat(k))
    debug(self,pprint.pformat(newcontent))
    debug(self,pprint.pformat(newusers))
    debug(self,pprint.pformat(newname))
    if k=="new":
      newsharekey=hashlib.md5("random9boGJFy1mY4nL56padding"+str(time.time)+os.urandom(10)).hexdigest()
      obj=Drawing(name=newname,owner=email,shared=newusers,content=newcontent,sharekey=newsharekey)
      key=obj.put()
      wrapwrite(self,'{"content":%s,"key":"%s"}'%(obj.content,obj.key.id()))
    else:
      key=ndb.Key('Drawing', int(k))
      obj=key.get()
      if not obj:
        wrapwrite(self,'{"error":"not found"}')
	return
      if not obj.shared:
        obj.shared=[]
      if email==obj.owner or email in obj.shared:
	pass
      else:
        wrapwrite(self,json.dumps({'error':'no access'}))
	return
      obj.content=newcontent
      obj.shared=newusers
      obj.name=newname
      obj.put()
      wrapwrite(self,'{"content":%s,"key":"%s"}'%(obj.content,obj.key.id()))

class DeleteHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/javascript'
    user = users.get_current_user()
    if not user:
      wrapwrite(self,json.dumps({'error':'not logged in at the sync server'}))
      return
    email=user.email().lower()
    k=self.request.GET['key']
    if k=='new':
      wrapwrite(self,json.dumps({'error':'drawing has not been saved yet?'}))
      return
    debug(self,"delete")
    debug(self,pprint.pformat(k))
    key=ndb.Key('Drawing', int(k))
    obj=key.get()
    if not obj:
      wrapwrite(self,json.dumps({'error':'not found'}))
      return
    #only the owner can delete. But anyone can save an empty drawing, so
    #this is for now pretty pointless. If some version control
    #is implemented, this makes more sense.
    if email==obj.owner:
      pass
    else:
      wrapwrite(self,json.dumps({'error':'no access'}))
      return
    key.delete()
    wrapwrite(self,'{"key":"%s"}'%(obj.key.id()))

debugstate = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes=[
    ('/list', ListHandler),
    ('/load', LoadHandler),
    ('/loadwithkey', LoadWithKeyHandler),
    ('/sync', SyncHandler),
    ('/delete', DeleteHandler),
    ('/test', TestHandler),
    ('/logout', LogoutHandler),
    ('/login', LoginHandler),
    ('/', RootHandler),
], debug=debugstate)
