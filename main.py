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
  shared = ndb.StringProperty(repeated=True)
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
      (user.email(),self.request.path_url, users.create_logout_url('http://www.google.com/')))

class TestHandler(webapp2.RequestHandler):
  def get(self):

    self.response.headers['Content-Type'] = 'text/html'   
    user = users.get_current_user()
    self.response.write("""
<!--
The following javascript example code here is public domain.
-->
You are now logged in as %s.
<p>
<script src='//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js'></script>
<script>
function create() {
  $('#item').html('Name: <input id=name value="New Drawing"> Content: <input id=content> Shared with: <input id=shared value="[]"><input id=key type=hidden value="new"> <button onclick="save()">Save</button> <p> Note: shared emails format is a json array: <tt>["email.address@example.com","another.address@example.com"]</tt>')
}

function del() {
  key=$('#key').val()
  name=$('#name').val()
  if (!confirm("Really delete " + escapehtml(name) + "?")) return
  $.post('/delete',{'key':key},function(data) {
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
    
  })
}

function save() {
  key=$('#key').val()
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
  $.post('/sync',{'key':key,'name':name,'content':content,'shared':shared},function(data) {
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
    
  })
}

function load(key) {
  $.getJSON('/load',{'key':key},function(data) {
    if(data.error) {
       alert("Could not load data: "+data.error)
       return
    }
    if(!data.content) {
       alert("Could not load data.")
       return
    }
    if (!data.name) data.name="(unnamed)"
    
    $('#item').html('Name: <input id=name value="'+escapehtml(data.name)+'"> Content: <input id=content> Shared with: <input id=shared><input id=key type=hidden value="'+key+'"> <button onclick="save()">Save</button><button onclick="del()">Delete</button> <p> Note: shared emails format is a json array: <tt>["email.address@example.com","another.address@example.com"]</tt>')
    $('#content').val(JSON.stringify(data.content))
    $('#shared').val(JSON.stringify(data.shared))
    
  })
}

function list() {
  $.getJSON('/list',function(data) {
    if(!data.own) {
       alert("Could not load data.")
       return
    }
    own=data.own
    shared=data.shared
    init()
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
<div id=list></div>
<div id=item></div>
<hr>

<p><a href="%s">Sign out</a>
<!--
public domain code ends.
-->
""" %
      (user.email(), users.create_logout_url('http://www.google.com/')))

class ListHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    mydrawings=Drawing.query(Drawing.owner==user.email().lower()).fetch()
    debug(self,"my")
    debug(self,pprint.pformat(mydrawings))
    own=[]
    for dr in mydrawings:
      own.append({'key':dr.key.id(),'name':dr.name})
      
    shareddrawings=Drawing.query(Drawing.shared==user.email().lower())
    debug(self,"shared")
    debug(self,pprint.pformat(shareddrawings))
    shared=[]
    for dr in shareddrawings:
      shared.append({'key':dr.key.id(),'name':dr.name})
    self.response.write(json.dumps({'own':own,'shared':shared}))
      

class LoadHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    key=ndb.Key('Drawing', int(self.request.GET['key']))
    obj=key.get()
    if not obj:
      self.response.write('{"error":"not found"}')
    else:
      if user.email().lower()==obj.owner or user.email().lower() in obj.shared:
        self.response.write('{"key":%s,"content":%s,"name":%s,"shared":%s}'%(self.request.GET['key'],obj.content,json.dumps(obj.name),json.dumps(obj.shared)))
      else:
        self.response.write('{"error":"no access"}')
        

class SyncHandler(webapp2.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    try:
      newname=self.request.POST['name']
    except KeyError:
      newname=''
    try:
      newusers=json.loads(self.request.POST['shared'])
    except KeyError:
      newusers=[]
    except ValueError:
      self.response.write('{"error":"invalid shared list"}')
      return
    newcontent=self.request.POST['content']

    k=self.request.POST['key']
    debug(self,"sync")
    debug(self,pprint.pformat(k))
    debug(self,pprint.pformat(newcontent))
    debug(self,pprint.pformat(newusers))
    debug(self,pprint.pformat(newname))
    if k=="new":
      obj=Drawing(name=newname,owner=user.email().lower(),shared=newusers,content=newcontent)
      key=obj.put()
      self.response.write('{"content":%s,"key":"%s"}'%(obj.content,obj.key.id()))
    else:
      key=ndb.Key('Drawing', int(k))
      obj=key.get()
      if not obj:
        self.response.write('{"error":"not found"}')
      if user.email().lower()==obj.owner or user.email().lower() in obj.shared:
	pass
      else:
        self.response.write('{"error":"no access"}')
	return
      obj.content=newcontent
      obj.shared=newusers
      obj.name=newname
      obj.put()
      self.response.write('{"content":%s,"key":"%s"}'%(obj.content,obj.key.id()))

class DeleteHandler(webapp2.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'application/json'   
    user = users.get_current_user()
    k=self.request.POST['key']
    debug(self,"delete")
    debug(self,pprint.pformat(k))
    key=ndb.Key('Drawing', int(k))
    obj=key.get()
    if not obj:
      self.response.write('{"error":"not found"}')
    if user.email().lower()==obj.owner:
      pass
    else:
      self.response.write('{"error":"no access"}')
      return
    key.delete()
    self.response.write('{"key":"%s"}'%(obj.key.id()))

debugstate = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes=[
    ('/list', ListHandler),
    ('/load', LoadHandler),
    ('/sync', SyncHandler),
    ('/delete', DeleteHandler),
    ('/test', TestHandler),
    ('/', RootHandler),
], debug=debugstate)
