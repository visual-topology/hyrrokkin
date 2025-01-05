#!/bin/bash

conda activate hyrrokkin-env
export PYTHONPATH=`pwd`/../src
mkdocs build
