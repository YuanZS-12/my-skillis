# NX CAD Advanced Geometry Roadmap

This roadmap is for reusable wrapper helpers. It does not ban raw NXOpen
journals from using loft, sweep, through-curve, spline, PMI, or other advanced
NX APIs when MCP API-review evidence supports the code. Wrapper acceptance
gates decide when helpers become reusable `NXBuilder` methods; they are not a
ceiling on what an agent may model with direct NXOpen.

## Principle

Do not add raw NXOpen geometry helpers from memory. Each helper needs an
official Siemens API source entry, a wrapper-level test, a generated journal
fixture, local static checks, and real NX runtime feedback before it is listed
as production-ready.

## Stage 1: Revolved Profiles

Use for hubs, cones, shafts, nozzles, grooves, rings, bearing seats, and
axisymmetric covers. Target wrapper:
`b.revolved_profile(points, axis_point, axis_direction, angle_degrees=360.0)`.

Status: locally implemented with official source map entries for
`CreateRevolveBuilder`, `RevolveBuilder`, `AxisCollection`, `Limits`, and
`Extend`. Still requires user- or automation-reported Siemens NX runtime
validation before being treated as broadly production-ready.

## Stage 2: Curve And Spline Primitives

Use for smooth blade centerlines, swept paths, wire paths, handles, tubing, and
guide curves. Target wrappers: `b.polyline_curve(...)`, `b.spline_curve(...)`.

## Stage 3: Loft Or Through-Curve Bodies

Use for blade surfaces, ducts, tapered housings, and non-axisymmetric shells.
Target wrapper: `b.loft_profiles(profile_sections, solid=True)`.

## Stage 4: Swept Profiles

Use for propeller blades, tubes, rails, curved ribs, seals, and ergonomic
handles. Target wrapper: `b.sweep_profile(profile_points, path_points, ...)`.

## Stage 5: Semantic Blade Helpers

Use for impeller, propeller, turbine, and blisk models. Target wrappers:
`b.airfoil_section(...)`, `b.lofted_blade(...)`, and
`b.revolved_impeller_hub(...)`.

## Acceptance Gates

- Official source map entry exists.
- Wrapper helper has a static checker allowance.
- Local Python tests pass.
- `models/cadnx/` sync check passes.
- User or automation reports NX runtime result for at least one fixture.
## NX 2606 Sweep API Generation

For NX 2606, do not create new recipes with the deprecated
`NXOpen.Features.SweptBuilder`. Siemens marks that class deprecated from NX
2412 and directs callers to `NXOpen.Features.SweptBuilder1`, created through
`work_part.Features.FreeformSurfaceCollection.CreateSweptBuilder1(...)`.

The first three `SweptBuilder1` probes deliberately separate:

1. one closed section + one intersecting guide + fixed orientation;
2. two closed sections + one corresponding-corner guide;
3. two corresponding sections with a rotated terminal section for twist.

NX 2606 manual evidence rejected the tested `ByAngularLaw` configurations on
both `SweptBuilder1` and the deprecated `SweptBuilder` with `Invalid orientation
method specified`. Do not label the rotated-section fallback as an angular-law
success. Use `nx2606.sweep.rotated-section-twist` when station geometry can
represent the intended twist, and keep `nx2606.sweep.angular-law` rejected
unless a materially different API recipe produces new evidence. A guide must
intersect its section; a guide that passes through empty profile interior is
not equivalent and may produce an invalid section-string failure.
