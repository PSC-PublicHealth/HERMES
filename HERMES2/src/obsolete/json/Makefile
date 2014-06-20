include ../localbuildpaths
PJC = $(PYJAMAS_ROOT)/bin/pyjsbuild
#PJCFLAGS = $(PJCDEBUG) --strict
PJCFLAGS = $(PJCDEBUG)

TARGETS = \
	output/hermes_ui.mozilla.cache.html output/hermes_ui.html output/hermes_ui.css \
	output/myjit.js output/hypergraphpanel_util.js output/treepanel_util.js \
        output/spacer.gif

#TARGETS = output/hermes_ui.mozilla.cache.html output/hermes_ui.html output/hermes_ui.css

HERMESPY = hermes_ui.py echoserviceinteractor.py xkcdserviceinteractor.py \
		serviceinteractor.py testserviceinteractor.py guruserviceinteractor.py storesinteractor.py \
		fileuploader.py hermesservices.py filecopydialog.py filerenamedialog.py filedownloader.py \
		somethinginteractor.py routesinteractor.py toolsinteractor.py resourcemanager.py \
		reportinteractor.py canviz.py canvizutil.py x11colors.py hermesservices.py toolpanel.py \
		fireworkspanel.py fwsvgpanel.py

HERMESJS = myjit.js hypergraphpanel_util.js treepanel_util.js

all: $(TARGETS)

output/myjit.js: myjit.js
	cp $^ output/.

output/hypergraphpanel_util.js: hypergraphpanel_util.js
	cp $^ output/.

output/treepanel_util.js: treepanel_util.js
	cp $^ output/.

output/mytest.mozilla.cache.html: mytest.py
	$(PJC) $(PJCFLAGS) mytest.py

output/hermes_ui.mozilla.cache.html: $(HERMESPY)
	$(PJC) $(PJCFLAGS) hermes_ui.py
	touch hermes_ui_proto.html

output/hermes_ui.html: hermes_ui_proto.html
	rm -f output/hermes_ui.html
	cp hermes_ui_proto.html output/hermes_ui.html
	cp hermes_ui_proto.html public/hermes_ui.html

output/jsimports.js: jsimports.js
	rm -f output/jsimports.js
	cp jsimports.js output

output/mytest.html public/mytest.html: mytest.html
	rm -f output/mytest.html
	cp mytest.html output
	cp mytest.html public

output/mytest.css public/mytest.css: mytest.css
	rm -f output/mytest.css
	cp mytest.css output
	cp mytest.css public

output/hermes_ui.css public/hermes_ui.css: hermes_ui.css
	rm -f output/hermes_ui.css
	cp hermes_ui.css output
	cp hermes_ui.css public

output/spacer.gif: spacer.gif
	cp spacer.gif output/spacer.gif

clean:
	rm -f $(HERMESPY:.py=.js) output/*
