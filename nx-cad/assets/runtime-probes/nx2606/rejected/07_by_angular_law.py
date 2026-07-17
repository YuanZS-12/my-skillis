"""Historical NX 2606 rejected fixture; do not hand off for another run.

This preserves the final explicit-spine ByAngularLaw API combination that the
user reported failing with ``Invalid orientation method specified``. The
production fallback is the parent directory's ``07_sweep_angular_law.py``.
"""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import add_line_to_section, closed_rectangle_section, line_section


RAW_NXOPEN_HIGH_FIDELITY = True
STATIC_ONLY_NXOPEN_REVIEW = {"status": "rejected by manual NX 2606 evidence"}


def rejected_operation(work_part):
    root = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    tip = closed_rectangle_section(work_part, 40.0, 10.0, 5.0)
    guide = line_section(
        work_part,
        NXOpen.Point3d(10.0, 5.0, 0.0),
        NXOpen.Point3d(10.0, 5.0, 40.0),
    )
    builder = work_part.Features.FreeformSurfaceCollection.CreateSweptBuilder1(
        NXOpen.Features.Swept.Null
    )
    try:
        builder.BodyPreference.BodyType = NXOpen.GeometricUtilities.FeatureOptions.BodyStyle.Solid
        builder.SectionList.Append([root, tip])
        builder.GuideList.Append(guide)
        add_line_to_section(
            work_part,
            builder.Spine,
            NXOpen.Point3d(10.0, 5.0, 0.0),
            NXOpen.Point3d(10.0, 5.0, 40.0),
        )
        angular_law = builder.OrientationMethod.AngularLaw
        angular_law.SetSpineIntoBuilder(builder.Spine)
        angular_law.LawType = NXOpen.GeometricUtilities.LawBuilder.Type.Linear
        angular_law.StartValue.RightHandSide = "0"
        angular_law.EndValue.RightHandSide = "20"
        builder.OrientationMethod.OrientationOption = (
            NXOpen.GeometricUtilities.OrientationMethodBuilder.OrientationOptions.ByAngularLaw
        )
        return builder.CommitFeature()
    finally:
        builder.Destroy()
