#!/bin/bash

set -e -o pipefail

APPDIR=/opt/app/usea

cleanup() {
    echo "Cleanup !"
}

trap cleanup EXIT

user=payload-nke

mkdir -p $APPDIR
echo "Fixing ownership fo files to $user"
chown -R $(id $user -u):$(id $user -g) $APPDIR

echo "Starting app..."

if [ ! -f $APPDIR/main.py ]; then
    echo "Setting dummy application entry 'main.py' with watchdog support"
    cp $(dirname $0)/main_default.py $APPDIR/main.py
fi

echo "Launching python app:"
while true
do
 su $user -c "cd $APPDIR && python main.py"
done

echo "Exiting"
