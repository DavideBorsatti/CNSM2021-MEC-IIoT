#!/bin/sh

set -eu

docker build --tag davideborsatti/cnsm-mqtt-pub:latest --network host .
