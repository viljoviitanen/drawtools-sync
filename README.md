drawtools-sync
==============

IITC drawtools plugin sync server for google appengine.

An external interface to the stored data is included at url server/test (http://drawtools-sync.appspot.com/test on the public server run by the author)

The corresponding draw tools plugin source code is at

https://github.com/viljoviitanen/ingress-intel-total-conversion/blob/drawtools-sync/plugins/draw-tools.user.js

An installable version of the plugin is at

https://viljoviitanen.nfshost.com/iitc/draw-tools.user.js

It should work at least on Firefox and Greasemonkey (I'm not sure if you need to have installed draw tools before. At least one fellow player was able to open a drawing I had made and shared with him...)

Quick instructions:

- open "DrawTools Opt" from right hand side blue box
- select "Sync Server"
- before trying anything else "Login at Sync Server".
- the sharing syntax is lousy (a raw json/python array of email addresses). Sorry about that :)

The UI and the code need a lot of polishing, this quick a proof of concept.

For now the server is hardcoded in the plugin, but you could easily run your own (provided you have some experience with google appengine) and change it from the plugin code. I would advise you not to store anything sensitive at my server, as I can see all the data in the server, it's stored plaintext.

