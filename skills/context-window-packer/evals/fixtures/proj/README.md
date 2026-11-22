# Parcel tracker

Parcel tracker is a small service that polls carrier feeds and stores the latest
status of each parcel. It exposes one HTTP endpoint, `GET /parcels/<id>`, which
returns the status, the last scan location and the estimated delivery date.

## Running

Start the service with `python app.py`. It reads `CARRIER_FEED_URL` from the
environment and refreshes every five minutes. Parcels that have not changed in
thirty days are archived by the nightly job.

## Known problems

The estimated delivery date is wrong for parcels that cross a time zone boundary
on the last leg. See `util.py` for the conversion helper that needs fixing.
