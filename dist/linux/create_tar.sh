TMPDIR=/tmp/hermesbuild

mkdir $TMPDIR
mkdir $TMPDIR/hermes_1.0/
cp -r ../../HERMES2 $TMPDIR/hermes_1.0/
cp README  run_hermes  setup_hermes $TMPDIR/hermes_1.0/
cp ../../HERMES2/LICENSE.txt $TMPDIR/hermes_1.0/
cd $TMPDIR
tar -cvzf hermes_1.0.tgz hermes_1.0
