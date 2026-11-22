# geo-pipeline

Loads municipal boundary files, normalises them and publishes tiles.

## Overview

The pipeline has three stages: load (geo/loader.py), normalise (geo/normalise.py) and publish (geo/publish.py).
It runs nightly. Input files arrive in an object store bucket; output tiles are written back.

## Quick start

    make install
    make dev-db
    make test
