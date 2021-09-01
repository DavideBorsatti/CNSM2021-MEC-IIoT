#!/bin/sh

set -eu

docker build --tag davideborsatti/cnsm-mep-iot:latest --network host .
