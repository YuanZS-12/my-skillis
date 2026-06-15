# NXOpen Create Block

For simple rectangular solids, prefer NXOpen block feature APIs when available.

The generated journal should define dimensions at the top:

    length = 100.0
    width = 60.0
    height = 20.0

For a centered block, use the lower corner:

    origin_x = -length / 2.0
    origin_y = -width / 2.0
    origin_z = 0.0

Then create a block from:

    corner = (origin_x, origin_y, origin_z)

to dimensions:

    length, width, height

If the exact NXOpen BlockFeatureBuilder API differs by NX version, use a journal recorded from the user's NX version as the authoritative template.

## Requirements

The created block must:

- Use millimeter units
- Be a solid body
- Have bounding box length x width x height
- Be saved as `.prt`
- Be exported as `.step` when possible
