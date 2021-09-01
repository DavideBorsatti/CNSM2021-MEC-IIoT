#!/bin/sh

set -eu

docker build --tag davideborsatti/cnsm-iot-client --network host .
