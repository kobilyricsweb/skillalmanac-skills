# Meeting notes, March

## Carrier feed

The carrier changed its feed format twice this quarter. The second change added
a free-text field that sometimes contains the pipe character, which is why the
scan parser joins the remaining parts back together. Nobody has confirmed that
the new format is stable, and the carrier gave no notice of either change.

## Hosting

The service runs on a single small instance. Memory use stays under 200 MB, and
the nightly archive job takes about four seconds. A move to a managed queue was
discussed and postponed until after the holiday season.

## Open questions

Who owns the on-call rota? Should the archive threshold be configurable per
carrier? Is the estimated delivery date shown to customers or only to support?
