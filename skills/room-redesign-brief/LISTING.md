# room-redesign-brief

## One line

Turns a measured room, its openings, budget, light and a few style words into a text brief, three image-tool prompts that repeat the same dimensions, and a measure-before-you-buy checklist.

## What it does

The skill runs a fixed nine-step procedure. It first records an intake table in which each value is marked given, assumed or missing. It then applies a clearance table with working values for walkways, the door swing arc, radiators, rug edges and the space under a window sill. From those values it derives a constraints table and splits the floor into named zones with areas in square metres.

Light is chosen from the window wall and the user's direct sun hours, using a short lookup table. Style is limited to three words and one palette sentence. The brief then produces exactly three image prompts. Each prompt copies the same dimension line, so a user comparing renderings can see which version changed the look and which kept the room intact.

The output ends with a checklist of what to measure before buying, and a list of every assumed or missing value for the user to confirm. The skill stops when the room length, width or a window wall is absent, and it declines structural, electrical, plumbing and floor-plan requests.

## When to use

Use it when someone has a room, a rough idea such as cozy or warm, and an image tool, and wants renderings that keep the real doorway, window and furniture sizes. It also fits a second pass after an earlier image came out with a sofa blocking a door.

## When not to use

Do not use it for building work, wiring, gas or plumbing, for contractor quotes, or for a to-scale floor plan. The output is not a measured drawing, and image tools can ignore the dimensions written in the prompt.

## Requirements

Any text-capable agent that can follow a Markdown procedure. No network access, no scripts and no extra tools are needed.

## Example

Excerpt from the offline smoke run (3.50 m by 4.00 m living room, north window). Full output is in VERIFICATION.md.

```
## Constraints
| Constraint | Working value | Source | Confirm |
| Main walkway width | 0.90 m minimum | derived | yes |
| Top of piece under window | 0.80 m max (0.10 m below 0.90 m sill) | derived | no |

### Variant A
Dimensions: room 3.50 m wide x 4.00 m long, ceiling 2.40 m (assumed); window 1.20 m wide, sill 0.90 m (assumed), north wall.
```

## Limits

Dimensions in the output are only as good as the intake. Ceiling height, window width and sill height are often guessed, and the skill marks them as assumed rather than checking them. The clearance values are working values chosen for this procedure and are not published standards. Light lines depend on the user's sun hours, which many people do not know. Style is limited to words the user supplies, so the skill cannot judge taste. Image tools may still draw furniture at the wrong scale.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
