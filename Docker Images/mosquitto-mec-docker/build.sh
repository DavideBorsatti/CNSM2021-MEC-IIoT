#!/bin/sh

set -eu

docker build --tag davideborsatti/cnsm-mep-mqtt:latest --network host .
