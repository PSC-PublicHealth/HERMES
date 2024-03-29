#uname=`uname`
#if [[$uname=="Darwin"]]; then pwd; fi

mkdir $TMPDIR/HERMES_dist
cp -r misc/template.app $TMPDIR/HERMES_dist/HERMES.app
cp -r ../../HERMES2 $TMPDIR/HERMES_dist/HERMES.app/Contents/Resources/

git clone https://github.com/andreyvit/create-dmg.git

mkdir -p build
./create-dmg/create-dmg \
--volname "HERMES" \
--volicon "misc/appIcon.icns" \
--background "misc/installer_background.png" \ 
--window-pos 200 120 \
--window-size 800 400 \
--icon-size 100 \
--icon $TMPDIR/HERMES_dist/HERMES.app 200 190 \
--eula $TMPDIR/HERMES_dist/HERMES.app/Contents/Resources/HERMES2/LICENSE.txt \
--hide-extension HERMES.app \
--app-drop-link 600 185 \
build/HERMES.dmg \
$TMPDIR/HERMES_dist

rm -r $TMPDIR/HERMES_dist
