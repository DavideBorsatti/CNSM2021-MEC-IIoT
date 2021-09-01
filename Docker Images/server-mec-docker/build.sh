#!/bin/sh

set -eu

docker build --tag lorenzobassi/opcua_server-mec:latest --network host .
