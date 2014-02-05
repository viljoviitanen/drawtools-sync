drawtools-sync
==============

IITC drawtools plugin sync server for google appengine.

An external interface to the stored data is included at url server/test (http://drawtools-sync.appspot.com/test on the public server run by the author)

The IITC plugin source is available at

https://github.com/viljoviitanen/drawtools-sync-plugin

An installable version of the plugin is at

https://viljoviitanen.nfshost.com/iitc/draw-tools-sync.user.js

It should work at least on Firefox and Greasemonkey. When writing this, you need to first have the "test version" of the draw tools plugin installed.

Quick instructions:

- open "DrawTools Sync" from right hand side blue box
- before trying anything else "Login at Sync Server".
- the sharing syntax is lousy (a raw json/python array of email addresses). Sorry about that :)

The UI and the code need a lot of polishing.

For now the server is hardcoded in the plugin, but you could easily run your own (provided you have some experience with google appengine) and change it from the plugin code. I would advise you not to store anything sensitive at my server, as I can see all the data in the server, it's stored plaintext.

