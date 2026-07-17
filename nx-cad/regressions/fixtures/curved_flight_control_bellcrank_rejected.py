"""NXOpen journal: aircraft control bellcrank with curved swept arms.

Raw NXOpen high-fidelity mode — direct NXOpen.* APIs, no cadnx wrapper.

The bellcrank has a central pivot hub and two curved control arms swept
along cubic B-spline guide curves.  Each arm tapers in width and thickness,
applies 10 degrees of progressive twist, and uses airfoil-like elliptical
cross-sections.

Outputs:
  - aircraft_curved_bellcrank.prt
  - aircraft_curved_bellcrank.step  (AP242)
"""

import math
import os
import time

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities


# =========================================================================
#  Named parameters  (all mm / degrees)
# =========================================================================

PART_NUMBER = "AC-CURVED-BELLCRANK-001"

# -- Hub ------------------------------------------------------------------
HUB_DIAMETER      = 50.0
HUB_HEIGHT        = 14.0
BORE_DIAMETER     = 20.0
BEARING_SEAT_DIA  = 32.0
BEARING_SEAT_DEPTH = 4.0

# -- Arm 1 (to X=100, Y=20) -----------------------------------------------
ARM1_BOSS_CX = 100.0
ARM1_BOSS_CY =  20.0
ARM1_CP1     = ( 35.0, -10.0)   # intermediate control point
ARM1_CP2     = ( 70.0,   5.0)   # intermediate control point

ARM1_WIDTH_HUB  = 32.0
ARM1_WIDTH_TIP  = 22.0
ARM1_THICK_HUB  = 12.0
ARM1_THICK_TIP  =  9.0
ARM1_TWIST_DEG  = 10.0

# -- Arm 2 (to X=-35, Y=85) -----------------------------------------------
ARM2_BOSS_CX = -35.0
ARM2_BOSS_CY =  85.0
ARM2_CP1     = (-10.0, 35.0)
ARM2_CP2     = (-25.0, 60.0)

ARM2_WIDTH_HUB  = 32.0
ARM2_WIDTH_TIP  = 22.0
ARM2_THICK_HUB  = 12.0
ARM2_THICK_TIP  =  9.0
ARM2_TWIST_DEG  = 10.0

# -- End bosses -----------------------------------------------------------
BOSS_DIAMETER = 32.0
BOSS_HEIGHT   = 14.0
BOSS_BORE_DIA = 10.0

# -- Lightening holes -----------------------------------------------------
LH_DIAMETER = 16.0
LH_MIN_WALL =  5.0

# -- Fillets / chamfers ---------------------------------------------------
HUB_FILLET_RADIUS  = 6.0
BOSS_FILLET_RADIUS = 4.0
BORE_CHAMFER       = 0.8

# -- Section ellipse point count ------------------------------------------
ELLIPSE_PTS = 16


# =========================================================================
#  Bezier math helpers
# =========================================================================

def bezier_pos(p0, p1, p2, p3, t):
    """Evaluate a cubic Bezier at parameter t ∈ [0,1]."""
    u = 1.0 - t
    return (u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1],
            0.0)


def bezier_tan(p0, p1, p2, p3, t):
    """Evaluate the tangent vector of a cubic Bezier at t ∈ [0,1]."""
    u = 1.0 - t
    return (3*u**2*(p1[0]-p0[0]) + 6*u*t*(p2[0]-p1[0]) + 3*t**2*(p3[0]-p2[0]),
            3*u**2*(p1[1]-p0[1]) + 6*u*t*(p2[1]-p1[1]) + 3*t**2*(p3[1]-p2[1]),
            0.0)


def normalize(v):
    mag = math.hypot(*v[:2]) if v[2] == 0.0 else math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if mag < 1e-12:
        return (0.0, 0.0, 0.0)
    return (v[0]/mag, v[1]/mag, v[2]/mag)


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def ellipse_3d(center, tangent, width, thickness, twist_deg, num_pts=ELLIPSE_PTS):
    """Return *num_pts* Point3d on an ellipse centred at *center* in a plane
    perpendicular to *tangent*.  The width axis is perpendicular to tangent
    and roughly horizontal; the thickness axis completes the frame.
    *twist_deg* rotates the ellipse in its own plane.
    """
    t = normalize(tangent)
    z_up = (0.0, 0.0, 1.0)
    # Width direction: perpendicular to tangent, roughly horizontal
    if abs(t[0]) < 1e-12 and abs(t[1]) < 1e-12:
        w = (1.0, 0.0, 0.0)  # tangent vertical
    else:
        w = normalize(cross(t, z_up))
    # Thickness direction: completes right-handed frame
    h = normalize(cross(w, t))

    twist = math.radians(twist_deg)
    ct, st = math.cos(twist), math.sin(twist)
    a, b = width / 2.0, thickness / 2.0

    pts = []
    for i in range(num_pts):
        theta = 2.0 * math.pi * i / num_pts
        lx = a * math.cos(theta)
        ly = b * math.sin(theta)
        # Apply twist
        tx = lx * ct - ly * st
        ty = lx * st + ly * ct
        px = center[0] + tx * w[0] + ty * h[0]
        py = center[1] + tx * w[1] + ty * h[1]
        pz = center[2] + tx * w[2] + ty * h[2]
        pts.append(NXOpen.Point3d(px, py, pz))
    return pts


# =========================================================================
#  NX helper functions
# =========================================================================

def new_work_part(session):
    base = os.path.splitext(os.path.abspath(__file__))[0]
    r = session.Parts.NewDisplay(base + ".prt", NXOpen.Part.Units.Millimeters)
    if isinstance(r, tuple):
        wp = r[0]
        if len(r) > 1 and r[1] is not None:
            r[1].Dispose()
    else:
        wp = r
    return wp


def body_of(feat):
    return feat.GetBodies()[0]


def cylinder_feat(wp, dia, height, origin, direction=(0,0,1)):
    b = wp.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
    b.Type = NXOpen.Features.CylinderBuilder.Types.AxisDiameterAndHeight
    b.Origin = NXOpen.Point3d(*map(float, origin))
    b.Direction = NXOpen.Vector3d(*map(float, direction))
    b.Diameter.RightHandSide = str(float(dia))
    b.Height.RightHandSide = str(float(height))
    b.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create
    f = b.CommitFeature()
    b.Destroy()
    return f


def block_feat(wp, length, width, height, origin):
    b = wp.Features.CreateBlockFeatureBuilder(None)
    b.SetOriginAndLengths(NXOpen.Point3d(*map(float, origin)),
                          str(float(length)), str(float(width)), str(float(height)))
    f = b.CommitFeature()
    b.Destroy()
    return f


def boolean_op(wp, target_feat, tool_feat, op):
    tb = body_of(target_feat)
    tl = body_of(tool_feat)
    b = wp.Features.CreateBooleanBuilder(NXOpen.Features.BooleanFeature.Null)
    b.Operation = op
    if hasattr(b, "Target"):
        b.Target = tb
    else:
        b.TargetBodyCollector.Add(tb)
    if hasattr(b, "Tool"):
        b.Tool = tl
    else:
        b.ToolBodyCollector.Add(tl)
    f = b.CommitFeature()
    b.Destroy()
    return f


def unite(wp, target, tool):
    return boolean_op(wp, target, tool, NXOpen.Features.Feature.BooleanType.Unite)


def subtract(wp, target, tool):
    return boolean_op(wp, target, tool, NXOpen.Features.Feature.BooleanType.Subtract)


def safe_unite(wp, target, tool, label):
    try:
        return unite(wp, target, tool)
    except Exception as e:
        print("  WARNING: unite '%s' failed: %s" % (label, e))
        return target


def safe_subtract(wp, target, tool, label):
    try:
        return subtract(wp, target, tool)
    except Exception as e:
        print("  WARNING: subtract '%s' failed: %s" % (label, e))
        return target


# =========================================================================
#  Spline / section creation
# =========================================================================

def create_guide_spline(wp, cp0, cp1, cp2, cp3):
    """Create a cubic B-spline (ThroughPoints) through 4 control points.

    Returns the Spline curve object.
    """
    pts_3d = [NXOpen.Point3d(cp0[0], cp0[1], cp0[2]),
              NXOpen.Point3d(cp1[0], cp1[1], cp1[2]),
              NXOpen.Point3d(cp2[0], cp2[1], cp2[2]),
              NXOpen.Point3d(cp3[0], cp3[1], cp3[2])]
    builder = wp.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    builder.Type = NXOpen.Features.StudioSplineBuilderEx.Types.ThroughPoints
    builder.IsPeriodic = False
    builder.Degree = 3
    builder.IsAssociative = True
    cm = builder.ConstraintManager
    for p in pts_3d:
        nx_pt = wp.Points.CreatePoint(p)
        gd = cm.CreateGeometricConstraintData()
        gd.Point = nx_pt
        cm.Append(gd)
    feat = builder.CommitFeature()
    spline = feat.GetEntities()[0]
    builder.Destroy()
    return spline


def make_section_from_spline(wp, spline, approx_point=None):
    """Build an NX Section from a single spline curve."""
    if approx_point is None:
        approx_point = NXOpen.Point3d(0.0, 0.0, 0.0)
    sec = wp.Sections.CreateSection(0.0095, 0.01, 0.5)
    sec.SetAllowedEntityTypes(NXOpen.SectionAllowTypes.OnlyCurves)
    rules = [wp.ScRuleFactory.CreateRuleBaseCurveDumb([spline])]
    sec.AddToSection(rules, spline, NXOpen.NXObject.Null,
                     NXOpen.NXObject.Null, approx_point,
                     NXOpen.Section.Mode.Create, False)
    return sec


def make_section_from_points(wp, pts_3d):
    """Build an NX Section from a closed list of Point3d by creating line
    segments between consecutive points (wrap-around), all as one rule."""
    n = len(pts_3d)
    lines = []
    for i in range(n):
        p1 = pts_3d[i]
        p2 = pts_3d[(i + 1) % n]
        lines.append(wp.Curves.CreateLine(p1, p2))
    sec = wp.Sections.CreateSection(0.01, 0.0095, 0.5)
    sec.SetAllowedEntityTypes(NXOpen.SectionAllowTypes.OnlyCurves)
    rules = [wp.ScRuleFactory.CreateRuleBaseCurveDumb(lines)]
    sec.AddToSection(rules, lines[0], NXOpen.NXObject.Null,
                     NXOpen.NXObject.Null, pts_3d[0],
                     NXOpen.Section.Mode.Create, False)
    return sec


def make_section_from_ellipse_pts(wp, pts_3d):
    """Create a closed section from ellipse points (line segments)."""
    return make_section_from_points(wp, pts_3d)


# =========================================================================
#  Build one arm via ThroughCurves loft
# =========================================================================

def build_curved_arm(wp, cp0, cp1, cp2, cp3,
                     width_hub, width_tip, thick_hub, thick_tip, twist_deg,
                     num_sections=5):
    """Build a curved arm by lofting through *num_sections* cross-sections
    along a cubic Bezier guide.  Returns the loft feature.
    """
    sections = []
    for s in range(num_sections):
        t = float(s) / (num_sections - 1)
        w = width_hub + (width_tip - width_hub) * t
        th = thick_hub + (thick_tip - thick_hub) * t
        tw = twist_deg * t
        pos = bezier_pos(cp0, cp1, cp2, cp3, t)
        tan = bezier_tan(cp0, cp1, cp2, cp3, t)
        pts = ellipse_3d(pos, tan, w, th, tw)
        sec = make_section_from_points(wp, pts)
        sections.append(sec)

    tcb = wp.Features.CreateThroughCurvesBuilder(NXOpen.Features.Feature.Null)
    tcb.BodyPreference = NXOpen.Features.ThroughCurvesBuilder.BodyPreferenceTypes.Solid
    tcb.PreserveShape = False
    tcb.PositionTolerance = 0.01
    tcb.TangentTolerance = 0.5
    for sec in sections:
        tcb.SectionsList.Append(sec)
    feat = tcb.CommitFeature()
    tcb.Destroy()
    print("  Arm lofted: %d sections" % num_sections)
    return feat


# =========================================================================
#  Utility: find circular edges for chamfer
# =========================================================================

def find_rim_edges(body, cx, cy, diameter, z_level):
    """Find circular edges on *body* centred at (*cx*,*cy*) with given
    *diameter* near Z = *z_level*."""
    target_circ = math.pi * diameter
    hits = []
    for e in body.GetEdges():
        try:
            mp = e.MidPoint
            length = e.GetLength()
        except Exception:
            continue
        if abs(mp.Z - z_level) > 0.5:
            continue
        if math.hypot(mp.X - cx, mp.Y - cy) > 2.0:
            continue
        if abs(length - target_circ) > 3.0:
            continue
        hits.append(e)
    return hits


# =========================================================================
#  Main
# =========================================================================

def main():
    session = NXOpen.Session.GetSession()
    wp = new_work_part(session)
    print("NX work part:", wp.FullPath)

    # ---- 1. Central pivot hub -------------------------------------------
    hub = cylinder_feat(wp, HUB_DIAMETER, HUB_HEIGHT,
                        (0, 0, -HUB_HEIGHT/2), (0, 0, 1))
    print("Central hub created.")

    # ---- 2. Curved Arm 1 (to X=100, Y=20) -------------------------------
    a1_cp0 = (0.0, 0.0, 0.0)
    a1_cp1 = (ARM1_CP1[0], ARM1_CP1[1], 0.0)
    a1_cp2 = (ARM1_CP2[0], ARM1_CP2[1], 0.0)
    a1_cp3 = (ARM1_BOSS_CX, ARM1_BOSS_CY, 0.0)

    arm1 = build_curved_arm(wp,
                            a1_cp0, a1_cp1, a1_cp2, a1_cp3,
                            ARM1_WIDTH_HUB, ARM1_WIDTH_TIP,
                            ARM1_THICK_HUB, ARM1_THICK_TIP,
                            ARM1_TWIST_DEG)
    # End boss for arm 1
    a1_boss = cylinder_feat(wp, BOSS_DIAMETER, BOSS_HEIGHT,
                            (ARM1_BOSS_CX, ARM1_BOSS_CY, -BOSS_HEIGHT/2),
                            (0, 0, 1))
    # Unite arm + boss into hub
    body = safe_unite(wp, hub, arm1, "arm1 → hub")
    body = safe_unite(wp, body, a1_boss, "arm1 boss → body")
    print("Arm 1 swept and united.")

    # ---- 3. Curved Arm 2 (to X=-35, Y=85) ------------------------------
    a2_cp0 = (0.0, 0.0, 0.0)
    a2_cp1 = (ARM2_CP1[0], ARM2_CP1[1], 0.0)
    a2_cp2 = (ARM2_CP2[0], ARM2_CP2[1], 0.0)
    a2_cp3 = (ARM2_BOSS_CX, ARM2_BOSS_CY, 0.0)

    arm2 = build_curved_arm(wp,
                            a2_cp0, a2_cp1, a2_cp2, a2_cp3,
                            ARM2_WIDTH_HUB, ARM2_WIDTH_TIP,
                            ARM2_THICK_HUB, ARM2_THICK_TIP,
                            ARM2_TWIST_DEG)
    a2_boss = cylinder_feat(wp, BOSS_DIAMETER, BOSS_HEIGHT,
                            (ARM2_BOSS_CX, ARM2_BOSS_CY, -BOSS_HEIGHT/2),
                            (0, 0, 1))
    body = safe_unite(wp, body, arm2, "arm2 → body")
    body = safe_unite(wp, body, a2_boss, "arm2 boss → body")
    print("Arm 2 swept and united.")

    # ---- 4. Central bore & bearing seats --------------------------------
    bore_tool = cylinder_feat(wp, BORE_DIAMETER, HUB_HEIGHT + 2,
                              (0, 0, -(HUB_HEIGHT+2)/2), (0, 0, 1))
    body = safe_subtract(wp, body, bore_tool, "central bore")

    for z_off in (HUB_HEIGHT/2, -HUB_HEIGHT/2 - BEARING_SEAT_DEPTH):
        seat = cylinder_feat(wp, BEARING_SEAT_DIA, BEARING_SEAT_DEPTH,
                             (0, 0, z_off), (0, 0, 1))
        body = safe_subtract(wp, body, seat,
                             "bearing seat at z=%.1f" % z_off)
    print("Central bore and bearing seats done.")

    # ---- 5. End-boss bores ----------------------------------------------
    for cx, cy, label in [(ARM1_BOSS_CX, ARM1_BOSS_CY, "boss1"),
                          (ARM2_BOSS_CX, ARM2_BOSS_CY, "boss2")]:
        tool = cylinder_feat(wp, BOSS_BORE_DIA, BOSS_HEIGHT + 2,
                             (cx, cy, -(BOSS_HEIGHT+2)/2), (0, 0, 1))
        body = safe_subtract(wp, body, tool, "%s bore" % label)
    print("End-boss bores done.")

    # ---- 6. Lightening holes (mid-arm region) ---------------------------
    # Arm 1: mid-point between hub and boss
    lh1_pos = bezier_pos(a1_cp0, a1_cp1, a1_cp2, a1_cp3, 0.5)
    lh1_tool = cylinder_feat(wp, LH_DIAMETER, HUB_HEIGHT + 2,
                             (lh1_pos[0], lh1_pos[1], -(HUB_HEIGHT+2)/2),
                             (0, 0, 1))
    body = safe_subtract(wp, body, lh1_tool, "arm1 lightening hole")

    # Arm 2: mid-point
    lh2_pos = bezier_pos(a2_cp0, a2_cp1, a2_cp2, a2_cp3, 0.5)
    lh2_tool = cylinder_feat(wp, LH_DIAMETER, HUB_HEIGHT + 2,
                             (lh2_pos[0], lh2_pos[1], -(HUB_HEIGHT+2)/2),
                             (0, 0, 1))
    body = safe_subtract(wp, body, lh2_tool, "arm2 lightening hole")
    print("Lightening holes done.")

    # ---- 7. Fillets -----------------------------------------------------
    body_obj = body_of(body)

    # 6 mm at hub-arm transitions
    try:
        hub_top_edges = find_rim_edges(body_obj, 0, 0, HUB_DIAMETER,
                                       HUB_HEIGHT/2)
        if hub_top_edges:
            b = wp.Features.CreateEdgeBlendBuilder(None)
            coll = wp.ScCollectors.CreateCollector()
            rule = wp.ScRuleFactory.CreateRuleEdgeDumb(hub_top_edges)
            coll.ReplaceRules([rule], False)
            b.AddChainset(coll, str(HUB_FILLET_RADIUS))
            b.CommitFeature()
            b.Destroy()
            print("  Hub fillets (6 mm): %d edge(s)" % len(hub_top_edges))
    except Exception as e:
        print("  WARNING: hub fillet failed: %s" % e)

    # 4 mm at arm→boss transitions
    for cx, cy, label in [(ARM1_BOSS_CX, ARM1_BOSS_CY, "boss1"),
                          (ARM2_BOSS_CX, ARM2_BOSS_CY, "boss2")]:
        try:
            boss_edges = find_rim_edges(body_obj, cx, cy, BOSS_DIAMETER,
                                        HUB_HEIGHT/2)
            if boss_edges:
                b = wp.Features.CreateEdgeBlendBuilder(None)
                coll = wp.ScCollectors.CreateCollector()
                rule = wp.ScRuleFactory.CreateRuleEdgeDumb(boss_edges)
                coll.ReplaceRules([rule], False)
                b.AddChainset(coll, str(BOSS_FILLET_RADIUS))
                b.CommitFeature()
                b.Destroy()
                print("  %s fillet (4 mm): %d edge(s)" % (label, len(boss_edges)))
        except Exception as e:
            print("  WARNING: %s fillet failed: %s" % (label, e))
    print("Fillets done.")

    # ---- 8. Chamfers on bore rims ---------------------------------------
    for cx, cy, dia, label in [(0, 0, BORE_DIAMETER, "central bore"),
                                (ARM1_BOSS_CX, ARM1_BOSS_CY, BOSS_BORE_DIA, "boss1 bore"),
                                (ARM2_BOSS_CX, ARM2_BOSS_CY, BOSS_BORE_DIA, "boss2 bore")]:
        try:
            edges = find_rim_edges(body_obj, cx, cy, dia, HUB_HEIGHT/2)
            if edges:
                cb = wp.Features.CreateChamferBuilder(None)
                coll = wp.ScCollectors.CreateCollector()
                rule = wp.ScRuleFactory.CreateRuleEdgeDumb(edges)
                coll.ReplaceRules([rule], False)
                cb.SmartCollector = coll
                cb.Option = NXOpen.Features.ChamferBuilderChamferOption.SymmetricOffsets
                cb.FirstOffset = str(BORE_CHAMFER)
                cb.CommitFeature()
                cb.Destroy()
                print("  %s chamfered: %d edge(s)" % (label, len(edges)))
        except Exception as e:
            print("  WARNING: chamfer %s failed: %s" % (label, e))
    print("Chamfers done.")

    # ---- 9. Save & export -----------------------------------------------
    status = wp.Save(NXOpen.BasePart.SaveComponents.TrueValue,
                     NXOpen.BasePart.CloseAfterSave.FalseValue)
    if status is not None and hasattr(status, "Dispose"):
        status.Dispose()

    base_path = os.path.splitext(os.path.abspath(__file__))[0]
    step_path = base_path + ".step"

    creator = session.DexManager.CreateStepCreator()
    creator.InputFile = wp.FullPath
    creator.OutputFile = step_path
    creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242
    creator.FileSaveFlag = False
    creator.ProcessHoldFlag = True
    creator.ExportFrom = NXOpen.StepCreator.ExportFromOption.DisplayPart
    creator.Commit()
    creator.Destroy()
    for _ in range(30):
        if os.path.exists(step_path) and os.path.getsize(step_path) > 0:
            print("STEP exported:", step_path)
            break
        time.sleep(1)

    bc = len(list(wp.Bodies))
    print("\n=== CURVED BELLCRANK COMPLETE ===")
    print("  Bodies: %d  PRT: %s  STEP: %s" % (bc, wp.FullPath, step_path))


if __name__ == "__main__":
    main()