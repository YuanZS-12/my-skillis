try:
    import inspect
    import os
    import sys
    import NXOpen
    import NXOpen.Features
    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False


class NXBuilder:
    """
    NX Open Python modeling wrapper.
    Must be instantiated inside a live NX session.
    Run the generated file via File -> Execute -> NX Open inside Siemens NX.
    All dimension arguments are converted to strings internally as required by NX Open builders.
    """

    def __init__(self, part_path=None, force_new_part=False):
        if not _NX_AVAILABLE:
            raise RuntimeError(
                "NXOpen is not available. "
                "Run this file on a machine with Siemens NX installed "
                "via File -> Execute -> NX Open."
            )
        self.session = NXOpen.Session.GetSession()
        self.part = self.session.Parts.Work
        if force_new_part:
            self.part = self._create_work_part(part_path)
        elif self.part is None:
            self.part = self._create_work_part(part_path)

    # Primitives

    CLEARANCE_HOLE_DIAMETERS = {
        "m2": 2.4,
        "m2.5": 2.9,
        "m3": 3.4,
        "m4": 4.5,
        "m5": 5.5,
        "m6": 6.6,
        "m8": 9.0,
        "m10": 11.0,
        "m12": 13.5,
    }

    TAP_DRILL_DIAMETERS = {
        "m2": 1.6,
        "m2.5": 2.05,
        "m3": 2.5,
        "m4": 3.3,
        "m5": 4.2,
        "m6": 5.0,
        "m8": 6.8,
        "m10": 8.5,
        "m12": 10.2,
    }

    SOCKET_HEAD_COUNTERBORES = {
        "m3": (6.5, 3.2),
        "m4": (8.0, 4.2),
        "m5": (9.5, 5.2),
        "m6": (11.0, 6.2),
        "m8": (15.0, 8.2),
        "m10": (18.0, 10.5),
        "m12": (20.0, 12.5),
    }

    FLAT_HEAD_COUNTERSINKS = {
        "m3": (6.3, 90.0),
        "m4": (8.4, 90.0),
        "m5": (10.4, 90.0),
        "m6": (12.5, 90.0),
        "m8": (16.5, 90.0),
        "m10": (20.5, 90.0),
    }

    DEFAULT_MIN_WALL = 1.0

    def require_positive(self, **values):
        """Validate that named generated parameters are positive real dimensions."""
        for name, value in values.items():
            if float(value) <= 0:
                raise ValueError(f"{name} must be positive.")

    def require_min_wall(self, local_width, feature_diameter, min_wall=None, label="feature"):
        """Validate positive side wall around a cylindrical feature."""
        min_wall = self.DEFAULT_MIN_WALL if min_wall is None else float(min_wall)
        side_wall = (float(local_width) - float(feature_diameter)) / 2.0
        if side_wall < min_wall:
            raise ValueError(
                f"{label} leaves {side_wall:.3f} mm side wall; "
                f"minimum is {min_wall:.3f} mm."
            )
        return side_wall

    def require_edge_distance(self, edge_distance, feature_diameter, min_ratio=1.0, label="feature"):
        """Validate distance from a feature center to the nearest external edge."""
        required = float(feature_diameter) * float(min_ratio)
        if float(edge_distance) < required:
            raise ValueError(
                f"{label} edge distance is {float(edge_distance):.3f} mm; "
                f"minimum is {required:.3f} mm."
            )
        return float(edge_distance)

    def require_feature_budget(
        self,
        *,
        boolean_operations=0,
        micro_holes=0,
        patterned_features=0,
        max_boolean_operations=120,
        max_micro_holes=120,
        max_patterned_features=96,
    ):
        """Validate generated-model complexity budgets before expensive NX booleans."""
        budgets = {
            "boolean_operations": (boolean_operations, max_boolean_operations),
            "micro_holes": (micro_holes, max_micro_holes),
            "patterned_features": (patterned_features, max_patterned_features),
        }
        for label, (actual, maximum) in budgets.items():
            actual = float(actual)
            maximum = float(maximum)
            if actual < 0 or maximum < 0:
                raise ValueError(f"{label} budget values must be nonnegative.")
            if actual > maximum:
                raise ValueError(f"{label}={actual:.0f} exceeds budget {maximum:.0f}.")
        return True

    def box(self, length, width, height, origin=(0, 0, 0)):
        """Create a rectangular block. Returns Feature."""
        self.require_positive(length=length, width=width, height=height)
        builder = self.part.Features.CreateBlockFeatureBuilder(None)
        builder.SetOriginAndLengths(
            self._point3d(origin),
            str(float(length)),
            str(float(width)),
            str(float(height)),
        )
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def cylinder(self, diameter, height, origin=(0, 0, 0), axis=(0, 0, 1)):
        """Create a cylinder. Returns Feature."""
        self.require_positive(diameter=diameter, height=height)
        builder = self.part.Features.CreateCylinderBuilder(None)
        cylinder_types = getattr(NXOpen.Features.CylinderBuilder, "Types", None)
        cylinder_type = self._enum_value(
            cylinder_types,
            "AxisDiameterAndHeight",
            "TypesAxisDiameterAndHeight",
        )
        if cylinder_type is not None:
            builder.Type = cylinder_type
        builder.Origin = self._point3d(origin)
        builder.Direction = self._vector3d(axis)
        self._set_expression(self._builder_member(builder, "Diameter"), diameter)
        self._set_expression(self._builder_member(builder, "Height"), height)
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def hole(self, diameter, depth, position=(0, 0, 0), direction=(0, 0, -1)):
        """
        Create a hole tool cylinder (subtractive).
        Must be followed by boolean_subtract(target, hole_feature).
        Returns Feature.
        """
        return self.cylinder(diameter, depth, origin=position, axis=direction)

    # Mechanical feature wrappers

    def clearance_diameter(self, screw_size):
        """Return normal metric clearance diameter for a screw size such as M3 or M6."""
        key = self._metric_key(screw_size)
        if key not in self.CLEARANCE_HOLE_DIAMETERS:
            raise ValueError(f"Unsupported clearance screw size: {screw_size}")
        return self.CLEARANCE_HOLE_DIAMETERS[key]

    def tap_drill_diameter(self, screw_size):
        """Return common coarse-thread tap drill diameter for a screw size such as M3 or M6."""
        key = self._metric_key(screw_size)
        if key not in self.TAP_DRILL_DIAMETERS:
            raise ValueError(f"Unsupported tapped screw size: {screw_size}")
        return self.TAP_DRILL_DIAMETERS[key]

    def screw_clearance_hole(self, target, screw_size, depth, position=(0, 0, 0), direction=(0, 0, -1)):
        """Cut a metric screw clearance hole. Returns the subtract feature."""
        tool = self.hole(
            self.clearance_diameter(screw_size),
            float(depth) + 2.0,
            position=position,
            direction=direction,
        )
        return self.boolean_subtract(target, tool)

    def tapped_hole(self, target, screw_size, depth, position=(0, 0, 0), direction=(0, 0, -1)):
        """
        Cut the tap-drill geometry for a metric tapped hole.

        NX thread annotation is intentionally not added here; this wrapper
        creates robust manufacturing-intent geometry for generated journals.
        """
        tool = self.hole(
            self.tap_drill_diameter(screw_size),
            float(depth) + 1.0,
            position=position,
            direction=direction,
        )
        return self.boolean_subtract(target, tool)

    def socket_head_counterbore_hole(
        self,
        target,
        screw_size,
        depth,
        position=(0, 0, 0),
        direction=(0, 0, -1),
    ):
        """Cut a metric socket-head clearance hole with a standard counterbore."""
        key = self._metric_key(screw_size)
        if key not in self.SOCKET_HEAD_COUNTERBORES:
            raise ValueError(f"Unsupported socket-head counterbore screw size: {screw_size}")
        counterbore_diameter, counterbore_depth = self.SOCKET_HEAD_COUNTERBORES[key]
        return self.counterbore_hole(
            target,
            self.clearance_diameter(key),
            float(depth) + 2.0,
            counterbore_diameter,
            counterbore_depth,
            position=position,
            direction=direction,
        )

    def countersink_hole(
        self,
        target,
        screw_size,
        depth,
        position=(0, 0, 0),
        direction=(0, 0, -1),
        head_diameter=None,
        angle_degrees=None,
    ):
        """
        Cut a clearance hole plus a simplified countersink relief.

        The relief is cylindrical by design in this compatibility wrapper.
        Use it to express manufacturing intent without relying on fragile
        generated conic/loft operations.
        """
        key = self._metric_key(screw_size)
        default = self.FLAT_HEAD_COUNTERSINKS.get(key)
        if head_diameter is None:
            if default is None:
                raise ValueError(f"Unsupported countersink screw size: {screw_size}")
            head_diameter = default[0]
        if angle_degrees is None:
            angle_degrees = default[1] if default is not None else 90.0

        result = self.screw_clearance_hole(target, key, depth, position=position, direction=direction)
        sink_depth = self._countersink_depth(head_diameter, self.clearance_diameter(key), angle_degrees)
        relief = self.hole(head_diameter, sink_depth + 0.5, position=position, direction=direction)
        self.boolean_subtract(target, relief)
        return result

    def rectangular_pocket(self, target, length, width, depth, center, direction=(0, 0, -1)):
        """Cut an axis-aligned rectangular pocket from a target body. Returns subtract feature."""
        direction = self._unit_vector(direction)
        center = self._tuple3(center)
        length = float(length)
        width = float(width)
        depth = float(depth)
        self.require_positive(length=length, width=width, depth=depth)
        origin = (
            center[0] - length / 2.0,
            center[1] - width / 2.0,
            center[2],
        )
        if self._is_axis(direction, (0, 0, -1)):
            cutter_origin = (origin[0], origin[1], center[2] - depth - 1.0)
            cutter_lengths = (length, width, depth + 1.0)
        elif self._is_axis(direction, (0, 0, 1)):
            cutter_origin = origin
            cutter_lengths = (length, width, depth + 1.0)
        else:
            raise ValueError("rectangular_pocket currently supports Z-axis directions only.")
        cutter = self.box(*cutter_lengths, origin=cutter_origin)
        return self.boolean_subtract(target, cutter)

    def linear_pattern_points(self, start, count, spacing, direction=(1, 0, 0)):
        """Return evenly spaced point tuples for generated hole/feature patterns."""
        count = int(count)
        if count < 1:
            raise ValueError("linear pattern count must be at least 1.")
        start = self._tuple3(start)
        direction = self._unit_vector(direction)
        return [
            self._add_vectors(start, self._scale_vector(direction, float(index) * float(spacing)))
            for index in range(count)
        ]

    def circular_pattern_points(self, center, radius, count, start_angle_degrees=0.0, z=None):
        """Return XY circular pattern points around center."""
        count = int(count)
        if count < 1:
            raise ValueError("circular pattern count must be at least 1.")
        cx, cy, cz = self._tuple3(center)
        if z is None:
            z = cz
        points = []
        for index in range(count):
            angle = self._radians(float(start_angle_degrees) + 360.0 * float(index) / float(count))
            points.append((cx + float(radius) * self._cos(angle), cy + float(radius) * self._sin(angle), float(z)))
        return points

    def slot_cut(self, target, length, width, depth, center, axis=(1, 0, 0), direction=(0, 0, -1)):
        """
        Cut a rounded-end slot from target using two cylinders and a joining box.

        The slot centerline follows axis. The cut direction is usually normal to
        the target face. Returns the most recent boolean subtract Feature.
        """
        length = float(length)
        width = float(width)
        depth = float(depth)
        if length < width:
            raise ValueError("slot_cut length must be greater than or equal to width.")

        axis = self._unit_vector(axis)
        direction = self._unit_vector(direction)
        center = self._tuple3(center)
        half_straight = max((length - width) / 2.0, 0.0)
        radius = width / 2.0
        start = self._add_vectors(center, self._scale_vector(axis, -half_straight))
        end = self._add_vectors(center, self._scale_vector(axis, half_straight))

        first = self.hole(width, depth + 2.0, position=start, direction=direction)
        result = self.boolean_subtract(target, first)
        second = self.hole(width, depth + 2.0, position=end, direction=direction)
        result = self.boolean_subtract(target, second)

        if half_straight > 0:
            bridge_lengths, box_origin = self._slot_bridge_box(
                center=center,
                axis=axis,
                direction=direction,
                length=length - width,
                width=width,
                depth=depth + 2.0,
            )
            bridge = self.box(*bridge_lengths, origin=box_origin)
            result = self.boolean_subtract(target, bridge)
        return result

    def counterbore_hole(
        self,
        target,
        hole_diameter,
        hole_depth,
        counterbore_diameter,
        counterbore_depth,
        position=(0, 0, 0),
        direction=(0, 0, -1),
    ):
        """Cut a through/blind hole plus a larger counterbore. Returns last subtract Feature."""
        through = self.hole(hole_diameter, float(hole_depth) + 2.0, position=position, direction=direction)
        result = self.boolean_subtract(target, through)
        counterbore = self.hole(
            counterbore_diameter,
            float(counterbore_depth) + 1.0,
            position=position,
            direction=direction,
        )
        return self.boolean_subtract(target, counterbore)

    def annular_groove(
        self,
        target,
        outer_diameter,
        inner_diameter,
        depth,
        position=(0, 0, 0),
        direction=(0, 0, -1),
        cutter_overlap=0.5,
    ):
        """Cut a ring-shaped groove with explicit inner and outer diameters."""
        outer_diameter = float(outer_diameter)
        inner_diameter = float(inner_diameter)
        depth = float(depth)
        cutter_overlap = float(cutter_overlap)
        self.require_positive(
            outer_diameter=outer_diameter,
            inner_diameter=inner_diameter,
            depth=depth,
            cutter_overlap=cutter_overlap,
        )
        if inner_diameter >= outer_diameter:
            raise ValueError("annular_groove inner_diameter must be smaller than outer_diameter.")

        direction = self._unit_vector(direction)
        position = self._tuple3(position)
        cutter_depth = depth + 2.0 * cutter_overlap
        cutter = self.cylinder(outer_diameter, cutter_depth, origin=position, axis=direction)
        inner_position = self._add_vectors(position, self._scale_vector(direction, -cutter_overlap))
        inner_void = self.hole(
            inner_diameter,
            cutter_depth + 2.0,
            position=inner_position,
            direction=direction,
        )
        cutter = self.boolean_subtract(cutter, inner_void)
        return self.boolean_subtract(target, cutter)

    def bearing_seat(
        self,
        target,
        bore_diameter,
        seat_diameter,
        through_depth,
        seat_depth,
        position=(0, 0, 0),
        direction=(0, 0, -1),
        cutter_overlap=0.5,
    ):
        """Cut a bearing bore with an explicit annular shoulder/seat relief."""
        bore_diameter = float(bore_diameter)
        seat_diameter = float(seat_diameter)
        through_depth = float(through_depth)
        seat_depth = float(seat_depth)
        cutter_overlap = float(cutter_overlap)
        self.require_positive(
            bore_diameter=bore_diameter,
            seat_diameter=seat_diameter,
            through_depth=through_depth,
            seat_depth=seat_depth,
            cutter_overlap=cutter_overlap,
        )
        if seat_diameter <= bore_diameter:
            raise ValueError("bearing_seat seat_diameter must be greater than bore_diameter.")
        direction = self._unit_vector(direction)
        position = self._tuple3(position)
        bore_position = self._add_vectors(position, self._scale_vector(direction, -cutter_overlap))
        bore = self.hole(
            bore_diameter,
            through_depth + 2.0 * cutter_overlap,
            position=bore_position,
            direction=direction,
        )
        self.boolean_subtract(target, bore)
        return self.annular_groove(
            target,
            outer_diameter=seat_diameter,
            inner_diameter=bore_diameter,
            depth=seat_depth,
            position=position,
            direction=direction,
            cutter_overlap=cutter_overlap,
        )

    def bushing_boss(
        self,
        target,
        boss_diameter,
        boss_height,
        bore_diameter,
        center,
        axis=(0, 0, 1),
        feature_overlap=0.5,
        through_overcut=1.0,
    ):
        """Unite a cylindrical bushing boss and cut its through bore."""
        boss_diameter = float(boss_diameter)
        boss_height = float(boss_height)
        bore_diameter = float(bore_diameter)
        feature_overlap = float(feature_overlap)
        through_overcut = float(through_overcut)
        self.require_positive(
            boss_diameter=boss_diameter,
            boss_height=boss_height,
            bore_diameter=bore_diameter,
            feature_overlap=feature_overlap,
            through_overcut=through_overcut,
        )
        self.require_min_wall(boss_diameter, bore_diameter, min_wall=self.DEFAULT_MIN_WALL, label="bushing boss")
        center = self._tuple3(center)
        axis = self._unit_vector(axis)
        boss_total_height = boss_height + feature_overlap
        boss_origin = self._add_vectors(center, self._scale_vector(axis, -boss_total_height / 2.0))
        boss = self.cylinder(boss_diameter, boss_total_height, origin=boss_origin, axis=axis)
        self.boolean_unite(target, boss)
        bore_depth = boss_height + 2.0 * through_overcut
        bore_origin = self._add_vectors(center, self._scale_vector(axis, -bore_depth / 2.0))
        bore = self.hole(bore_diameter, bore_depth, position=bore_origin, direction=axis)
        return self.boolean_subtract(target, bore)

    def clevis(
        self,
        target,
        length,
        width,
        ear_thickness,
        gap,
        pin_hole_diameter,
        center,
        u_axis=(1, 0, 0),
        v_axis=(0, 1, 0),
        w_axis=(0, 0, 1),
        feature_overlap=0.5,
        through_overcut=1.0,
    ):
        """Create a simplified two-ear clevis with a through pin hole."""
        length = float(length)
        width = float(width)
        ear_thickness = float(ear_thickness)
        gap = float(gap)
        pin_hole_diameter = float(pin_hole_diameter)
        feature_overlap = float(feature_overlap)
        through_overcut = float(through_overcut)
        self.require_positive(
            length=length,
            width=width,
            ear_thickness=ear_thickness,
            gap=gap,
            pin_hole_diameter=pin_hole_diameter,
            feature_overlap=feature_overlap,
            through_overcut=through_overcut,
        )
        self.require_min_wall(width, pin_hole_diameter, min_wall=self.DEFAULT_MIN_WALL, label="clevis pin hole")
        center = self._tuple3(center)
        u_axis = self._unit_vector(u_axis)
        v_axis = self._unit_vector(v_axis)
        w_axis = self._unit_vector(w_axis)
        self._require_orthogonal_axes(u_axis, v_axis, w_axis)

        ear_offset = gap / 2.0 + ear_thickness / 2.0
        for sign in (-1.0, 1.0):
            ear_center = self._add_vectors(center, self._scale_vector(w_axis, sign * ear_offset))
            ear = self.oriented_box(
                length,
                width,
                ear_thickness + feature_overlap,
                center=ear_center,
                u_axis=u_axis,
                v_axis=v_axis,
                w_axis=w_axis,
            )
            self.boolean_unite(target, ear)

        hole_center = self._add_vectors(center, self._scale_vector(u_axis, length / 2.0))
        total_depth = gap + 2.0 * ear_thickness + 2.0 * through_overcut
        hole_start = self._add_vectors(hole_center, self._scale_vector(w_axis, -total_depth / 2.0))
        pin_hole = self.hole(
            pin_hole_diameter,
            total_depth,
            position=hole_start,
            direction=w_axis,
        )
        return self.boolean_subtract(target, pin_hole)

    def import_step_part(
        self,
        step_path,
        name=None,
        *,
        flatten=True,
        sew=True,
        optimize=False,
        simplify=False,
        smooth_bsurfaces=True,
        layer=0,
    ):
        """
        Import an external STEP file into the current work part.

        This uses the official NXOpen DexManager Step214Importer path. It
        returns committed objects when NX reports them, otherwise the Commit()
        return value.
        """
        importer = self._create_step214_importer()
        try:
            input_path = str(step_path)
            self._call_or_set(importer, "InputFile", input_path)
            self._call_or_set(importer, "FileOpenFlag", False)
            self._call_or_set(importer, "ProcessHoldFlag", True)
            self._call_or_set(importer, "FlattenAssembly", bool(flatten))
            self._call_or_set(importer, "SewSurfaces", bool(sew))
            self._call_or_set(importer, "Optimize", bool(optimize))
            self._call_or_set(importer, "SimplifyGeometry", bool(simplify))
            self._call_or_set(importer, "SmoothBSurfaces", bool(smooth_bsurfaces))
            self._call_or_set(importer, "LayerDefault", int(layer))
            import_to_option = self._enum_value(
                getattr(NXOpen.Step214Importer, "ImportToOption", None),
                "WorkPart",
            )
            if import_to_option is not None:
                self._call_or_set(importer, "ImportTo", import_to_option)
            committed = importer.Commit()
            if hasattr(importer, "GetCommittedObjects"):
                committed_objects = importer.GetCommittedObjects()
                if committed_objects:
                    committed = list(committed_objects)
            if name:
                print(f"Imported STEP component {name}: {input_path}")
            else:
                print(f"Imported STEP component: {input_path}")
            return committed
        finally:
            if hasattr(importer, "Destroy"):
                importer.Destroy()

    def add_component(self, step_path, name=None, **placement):
        """Guarded contract for adding an external STEP part as an assembly component."""
        raise self._external_component_not_implemented(
            "add_component",
            step_path=step_path,
            name=name,
            placement=placement,
        )

    def place_component(
        self,
        component,
        origin=(0, 0, 0),
        x_axis=(1, 0, 0),
        z_axis=(0, 0, 1),
    ):
        """Guarded contract for placing imported STEP bodies or assembly components."""
        raise self._external_component_not_implemented(
            "place_component",
            component=component,
            origin=origin,
            x_axis=x_axis,
            z_axis=z_axis,
        )

    def rounded_box(self, length, width, height, radius=0, origin=(0, 0, 0), vertical_only=True):
        """
        Create a box and apply conservative cosmetic edge blends.

        Returns the base box feature even when some blends are skipped.
        """
        body = self.box(length, width, height, origin=origin)
        radius = float(radius)
        if radius <= 0:
            return body
        if vertical_only:
            edges = self.get_edges_by_axis(body, axis=(0, 0, 1))
        else:
            edges = self.get_all_edges(body)
        self.fillet(edges, radius)
        return body

    def oriented_box(
        self,
        length,
        width,
        height,
        center,
        u_axis=(1, 0, 0),
        v_axis=(0, 1, 0),
        w_axis=(0, 0, 1),
    ):
        """
        Create a rectangular prism in a local orthonormal coordinate frame.

        The box is centered at center. length follows u_axis, width follows
        v_axis, and height follows w_axis.
        """
        length = float(length)
        width = float(width)
        height = float(height)
        self.require_positive(length=length, width=width, height=height)
        center = self._tuple3(center)
        u_axis = self._unit_vector(u_axis)
        v_axis = self._unit_vector(v_axis)
        w_axis = self._unit_vector(w_axis)
        self._require_orthogonal_axes(u_axis, v_axis, w_axis)

        base_center = self._add_vectors(center, self._scale_vector(w_axis, -height / 2.0))
        points = [
            (-length / 2.0, -width / 2.0),
            (length / 2.0, -width / 2.0),
            (length / 2.0, width / 2.0),
            (-length / 2.0, width / 2.0),
        ]
        return self.polygon_prism_on_plane(
            points,
            height,
            origin=base_center,
            u_axis=u_axis,
            v_axis=v_axis,
            extrude_axis=w_axis,
        )

    def extrude(self, curves, distance, direction=(0, 0, 1)):
        """Extrude a list of curves by distance. Returns Feature."""
        builder = self.part.Features.CreateExtrudeBuilder(None)
        builder.Direction = self._vector3d(direction)
        builder.Limits.StartExtend.Value.RightHandSide = "0"
        builder.Limits.EndExtend.Value.RightHandSide = str(float(distance))
        for curve in curves:
            builder.SectionLines.Add(curve)
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def polygon_prism(self, points, distance, origin=(0, 0, 0), axis=(0, 0, 1)):
        """
        Create a solid prism from a closed planar polygon.

        Points are local XY tuples relative to origin. The polygon is extruded
        along axis by distance. Returns Feature.
        """
        if len(points) < 3:
            raise ValueError("polygon_prism requires at least three points.")

        ox, oy, oz = origin
        curves = []
        absolute_points = [
            NXOpen.Point3d(float(ox + x), float(oy + y), float(oz))
            for x, y in points
        ]
        for index, start in enumerate(absolute_points):
            end = absolute_points[(index + 1) % len(absolute_points)]
            curves.append(self.part.Curves.CreateLine(start, end))

        section = self.part.Sections.CreateSection(0.0095, 0.01, 0.5)
        for curve in curves:
            rule = self.part.ScRuleFactory.CreateRuleCurveDumb([curve])
            help_point = curve.StartPoint
            section.AddToSection(
                [rule],
                curve,
                None,
                None,
                help_point,
                NXOpen.Section.Mode.Create,
                False,
            )

        builder = self.part.Features.CreateExtrudeBuilder(None)
        builder.Section = section
        direction = self.part.Directions.CreateDirection(
            self._point3d(origin),
            self._vector3d(axis),
            NXOpen.SmartObject.UpdateOption.WithinModeling,
        )
        builder.Direction = direction
        builder.Limits.StartExtend.Value.RightHandSide = "0"
        builder.Limits.EndExtend.Value.RightHandSide = str(float(distance))
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def polygon_prism_on_plane(
        self,
        points,
        distance,
        origin=(0, 0, 0),
        u_axis=(1, 0, 0),
        v_axis=(0, 1, 0),
        extrude_axis=(0, 0, 1),
    ):
        """
        Create a solid prism from a closed polygon on an arbitrary local UV plane.

        Points are local (u, v) tuples relative to origin. The polygon is
        extruded along extrude_axis by distance. Returns Feature.
        """
        if len(points) < 3:
            raise ValueError("polygon_prism_on_plane requires at least three points.")

        ox, oy, oz = origin
        ux, uy, uz = u_axis
        vx, vy, vz = v_axis
        absolute_points = []
        for u, v in points:
            absolute_points.append(
                NXOpen.Point3d(
                    float(ox + u * ux + v * vx),
                    float(oy + u * uy + v * vy),
                    float(oz + u * uz + v * vz),
                )
            )

        curves = []
        for index, start in enumerate(absolute_points):
            end = absolute_points[(index + 1) % len(absolute_points)]
            curves.append(self.part.Curves.CreateLine(start, end))

        section = self.part.Sections.CreateSection(0.0095, 0.01, 0.5)
        for curve in curves:
            rule = self.part.ScRuleFactory.CreateRuleCurveDumb([curve])
            section.AddToSection(
                [rule],
                curve,
                None,
                None,
                curve.StartPoint,
                NXOpen.Section.Mode.Create,
                False,
            )

        builder = self.part.Features.CreateExtrudeBuilder(None)
        builder.Section = section
        direction = self.part.Directions.CreateDirection(
            self._point3d(origin),
            self._vector3d(extrude_axis),
            NXOpen.SmartObject.UpdateOption.WithinModeling,
        )
        builder.Direction = direction
        builder.Limits.StartExtend.Value.RightHandSide = "0"
        builder.Limits.EndExtend.Value.RightHandSide = str(float(distance))
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def revolved_profile(self, points, axis_point=(0, 0, 0), axis_direction=(0, 0, 1), angle_degrees=360.0):
        """
        Create a revolved solid from radial/Z profile points.

        `points` are `(radius, z)` pairs relative to `axis_point` and
        `axis_direction`. The profile is closed automatically and revolved by
        `angle_degrees`. Returns Feature.
        """
        if len(points) < 3:
            raise ValueError("revolved_profile requires at least three profile points.")
        angle_degrees = float(angle_degrees)
        if angle_degrees <= 0.0 or angle_degrees > 360.0:
            raise ValueError("revolved_profile angle_degrees must be in (0, 360].")

        axis_point = self._tuple3(axis_point)
        axis_direction = self._unit_vector(axis_direction)
        radial_axis = self._perpendicular_unit(axis_direction)

        absolute_points = []
        for radius, z_offset in points:
            radius = float(radius)
            z_offset = float(z_offset)
            if radius < 0.0:
                raise ValueError("revolved_profile radius values must be nonnegative.")
            absolute_points.append(
                self._add_vectors(
                    self._add_vectors(axis_point, self._scale_vector(radial_axis, radius)),
                    self._scale_vector(axis_direction, z_offset),
                )
            )

        curves = []
        for index, start_tuple in enumerate(absolute_points):
            end_tuple = absolute_points[(index + 1) % len(absolute_points)]
            curves.append(self.part.Curves.CreateLine(self._point3d(start_tuple), self._point3d(end_tuple)))

        section = self.part.Sections.CreateSection(0.0095, 0.01, 0.5)
        for curve in curves:
            rule = self.part.ScRuleFactory.CreateRuleCurveDumb([curve])
            section.AddToSection(
                [rule],
                curve,
                None,
                None,
                curve.StartPoint,
                NXOpen.Section.Mode.Create,
                False,
            )

        builder = self.part.Features.CreateRevolveBuilder(None)
        builder.Section = section
        axis = self.part.Axes.CreateAxis(
            self._point3d(axis_point),
            self._vector3d(axis_direction),
            NXOpen.SmartObject.UpdateOption.WithinModeling,
        )
        builder.Axis = axis
        builder.Limits.StartExtend.Value.RightHandSide = "0"
        builder.Limits.EndExtend.Value.RightHandSide = str(angle_degrees)
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    # Boolean operations

    def boolean_subtract(self, target, tool):
        """Subtract tool body from target body. Returns Feature."""
        builder = self.part.Features.CreateBooleanBuilder(None)
        builder.Operation = NXOpen.Features.Feature.BooleanType.Subtract
        self._set_boolean_bodies(builder, self._body(target), self._body(tool))
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    def boolean_unite(self, target, tool):
        """Unite tool body into target body. Returns Feature."""
        builder = self.part.Features.CreateBooleanBuilder(None)
        builder.Operation = NXOpen.Features.Feature.BooleanType.Unite
        self._set_boolean_bodies(builder, self._body(target), self._body(tool))
        feature = builder.CommitFeature()
        builder.Destroy()
        return feature

    # Feature operations

    def fillet(self, edges, radius):
        """Apply constant-radius fillet to a list of edges. Returns Feature."""
        edges = list(edges)
        if not edges:
            return None

        radius_text = str(float(radius))
        feature = self._try_fillet_edges(edges, radius_text)
        if feature is not None:
            return feature

        successful_features = []
        for edge in edges:
            feature = self._try_fillet_edges([edge], radius_text, warn=False)
            if feature is not None:
                successful_features.append(feature)

        if successful_features:
            print(
                "WARNING: some fillet edges failed; applied fillet to "
                f"{len(successful_features)} of {len(edges)} edge(s)."
            )
            return successful_features[-1]

        print(
            "WARNING: skipping fillet because NX could not apply radius "
            f"{radius_text} to the selected edge set. Try reducing the radius."
        )
        return None

    def _try_fillet_edges(self, edges, radius_text, warn=True):
        builder = self.part.Features.CreateEdgeBlendBuilder(None)
        try:
            add_constant_radius_edge = getattr(builder, "AddConstantRadiusEdge", None)
            if add_constant_radius_edge is not None:
                for edge in edges:
                    add_constant_radius_edge(edge, radius_text)
            else:
                self._add_edge_blend_chainset(builder, edges, radius_text)
            feature = builder.CommitFeature()
            return feature
        except Exception as exc:
            if warn:
                print(
                    "WARNING: fillet failed for selected edge set at radius "
                    f"{radius_text}: {exc}"
                )
            return None
        finally:
            builder.Destroy()

    def chamfer(self, edges, offset):
        """Apply symmetric chamfer to a list of edges. Returns Feature."""
        edges = list(edges)
        if not edges:
            return None

        offset_text = str(float(offset))
        feature = self._try_chamfer_edges(edges, offset_text)
        if feature is not None:
            return feature

        successful_features = []
        for edge in edges:
            feature = self._try_chamfer_edges([edge], offset_text, warn=False)
            if feature is not None:
                successful_features.append(feature)

        if successful_features:
            print(
                "WARNING: some chamfer edges failed; applied chamfer to "
                f"{len(successful_features)} of {len(edges)} edge(s)."
            )
            return successful_features[-1]

        print(
            "WARNING: skipping chamfer because NX could not apply offset "
            f"{offset_text} to the selected edge set. Try reducing the offset."
        )
        return None

    def _try_chamfer_edges(self, edges, offset_text, warn=True):
        builder = self.part.Features.CreateChamferBuilder(None)
        try:
            option_class = getattr(NXOpen.Features.ChamferBuilder, "ChamferOption", None)
            symmetric_offsets = self._enum_value(option_class, "SymmetricOffsets")
            if symmetric_offsets is not None and hasattr(builder, "Option"):
                builder.Option = symmetric_offsets
            if hasattr(builder, "FirstOffset"):
                builder.FirstOffset = offset_text
            if hasattr(builder, "SecondOffset"):
                builder.SecondOffset = offset_text

            self._set_chamfer_edges(builder, edges)
            feature = builder.CommitFeature()
            return feature
        except Exception as exc:
            if warn:
                print(
                    "WARNING: chamfer failed for selected edge set at offset "
                    f"{offset_text}: {exc}"
                )
            return None
        finally:
            builder.Destroy()

    # Edge selection helpers

    def get_all_edges(self, feature):
        """Return all edges of a feature's body."""
        return list(self._body(feature).GetEdges())

    def get_top_edges(self, feature):
        """Return edges on the highest-Z face of a feature's body."""
        body = self._body(feature)
        return self._edges_on_z_extreme(body, highest=True)

    def get_bottom_edges(self, feature):
        """Return edges on the lowest-Z face of a feature's body."""
        body = self._body(feature)
        return self._edges_on_z_extreme(body, highest=False)

    def get_edges_by_axis(self, feature, axis=(0, 0, 1), tolerance=1e-5):
        """Return edges whose endpoints run parallel to axis."""
        body = self._body(feature)
        axis = self._unit_vector(axis)
        selected = []
        for edge in body.GetEdges():
            points = self._edge_vertices(edge)
            if len(points) != 2:
                continue
            edge_vector = (
                points[1].X - points[0].X,
                points[1].Y - points[0].Y,
                points[1].Z - points[0].Z,
            )
            if self._length(edge_vector) <= 1e-12:
                continue
            edge_axis = self._unit_vector(edge_vector)
            if abs(abs(self._dot(edge_axis, axis)) - 1.0) <= tolerance:
                selected.append(edge)
        return selected

    def get_edges_near(self, feature, point, tolerance):
        """Return edges with both endpoints within tolerance of point."""
        body = self._body(feature)
        point = self._tuple3(point)
        tolerance = float(tolerance)
        selected = []
        for edge in body.GetEdges():
            points = self._edge_vertices(edge)
            if len(points) != 2:
                continue
            if all(self._distance(self._point_tuple(vertex), point) <= tolerance for vertex in points):
                selected.append(edge)
        return selected

    def get_edges_in_box(self, feature, min_xyz, max_xyz):
        """Return linear edges whose vertices lie inside an axis-aligned box."""
        body = self._body(feature)
        selected = []
        min_x, min_y, min_z = min_xyz
        max_x, max_y, max_z = max_xyz
        for edge in body.GetEdges():
            points = self._edge_vertices(edge)
            if len(points) != 2:
                continue
            if all(
                min_x <= point.X <= max_x
                and min_y <= point.Y <= max_y
                and min_z <= point.Z <= max_z
                for point in points
            ):
                selected.append(edge)
        return selected

    # Export

    def export_step(self, output_path: str):
        """Export the current work part as STEP to output_path."""
        output_path = self._resolve_step_output_path(output_path)
        input_path = self._ensure_saved_part_for_export(output_path)
        exporter = self._create_step_exporter()
        self._configure_step_exporter(exporter, input_path, output_path)
        print(f"STEP export input PRT: {input_path}")
        print(f"STEP export output: {output_path}")
        if hasattr(exporter, "Validate") and not exporter.Validate():
            exporter.Destroy()
            raise RuntimeError(f"NX STEP exporter validation failed: {output_path}")
        exporter.Commit()
        exporter.Destroy()
        if not os.path.exists(output_path):
            recovered_path = self._recover_step_output(output_path)
            if recovered_path:
                print(f"STEP exporter wrote alternate file: {recovered_path}")
            else:
                raise RuntimeError(
                    "NX STEP exporter finished but the STEP file was not found: "
                    f"{output_path}"
                )
        print(f"STEP exported: {output_path}")

    def _configure_step_exporter(self, exporter, input_path, output_path):
        generic_creator = self._is_generic_step_creator(exporter)
        if generic_creator:
            self._set_step_export_as_ap242(exporter)
            self._set_export_from_display_part(exporter)
            self._enable_step_solid_export(exporter)
        else:
            self._set_step_export_as_ap214(exporter)
        self._set_export_destination_to_file(exporter)
        if input_path and not generic_creator:
            self._set_optional_attr(exporter, "InputFile", input_path)
        self._set_optional_attr(exporter, "OutputFile", output_path)
        self._set_optional_attr(exporter, "OutputFileExtension", "step")
        self._set_optional_attr(exporter, "FileSaveFlag", False)
        self._set_optional_attr(exporter, "ProcessHoldFlag", True)
        self._set_optional_attr(exporter, "LayerMask", "1-256")

    # Internal helpers

    def _point3d(self, values):
        x, y, z = values
        return NXOpen.Point3d(float(x), float(y), float(z))

    def _vector3d(self, values):
        x, y, z = values
        return NXOpen.Vector3d(float(x), float(y), float(z))

    def _tuple3(self, values):
        x, y, z = values
        return (float(x), float(y), float(z))

    def _add_vectors(self, first, second):
        return tuple(a + b for a, b in zip(first, second))

    def _scale_vector(self, values, scale):
        return tuple(float(value) * float(scale) for value in values)

    def _dot(self, first, second):
        return sum(a * b for a, b in zip(first, second))

    def _cross(self, first, second):
        ax, ay, az = first
        bx, by, bz = second
        return (
            ay * bz - az * by,
            az * bx - ax * bz,
            ax * by - ay * bx,
        )

    def _require_orthogonal_axes(self, u_axis, v_axis, w_axis, tolerance=1e-6):
        pairs = (
            ("u_axis", "v_axis", u_axis, v_axis),
            ("u_axis", "w_axis", u_axis, w_axis),
            ("v_axis", "w_axis", v_axis, w_axis),
        )
        for first_name, second_name, first, second in pairs:
            if abs(self._dot(first, second)) > tolerance:
                raise ValueError(f"{first_name} and {second_name} must be orthogonal.")
        handed = self._dot(self._cross(u_axis, v_axis), w_axis)
        if abs(abs(handed) - 1.0) > tolerance:
            raise ValueError("u_axis, v_axis, and w_axis must form an orthonormal frame.")

    def _length(self, values):
        return sum(value * value for value in values) ** 0.5

    def _distance(self, first, second):
        return self._length(tuple(a - b for a, b in zip(first, second)))

    def _unit_vector(self, values):
        values = self._tuple3(values)
        length = self._length(values)
        if length <= 1e-12:
            raise ValueError("Vector length must be nonzero.")
        return tuple(value / length for value in values)

    def _perpendicular_unit(self, values):
        axis = self._unit_vector(values)
        reference = (1.0, 0.0, 0.0)
        if abs(self._dot(axis, reference)) > 0.9:
            reference = (0.0, 1.0, 0.0)
        return self._unit_vector(self._cross(axis, reference))

    def _metric_key(self, screw_size):
        text = str(screw_size).strip().lower().replace(" ", "")
        if not text.startswith("m"):
            text = "m" + text
        return text

    def _is_axis(self, first, second, tolerance=1e-6):
        first = self._unit_vector(first)
        second = self._unit_vector(second)
        return self._distance(first, second) <= tolerance

    def _countersink_depth(self, head_diameter, clearance_diameter, angle_degrees):
        head_diameter = float(head_diameter)
        clearance_diameter = float(clearance_diameter)
        angle_degrees = float(angle_degrees)
        if head_diameter <= clearance_diameter:
            raise ValueError("countersink head diameter must exceed clearance diameter.")
        if angle_degrees <= 0 or angle_degrees >= 180:
            raise ValueError("countersink angle must be between 0 and 180 degrees.")
        math = __import__("math")
        return (head_diameter - clearance_diameter) / (2.0 * math.tan(math.radians(angle_degrees) / 2.0))

    def _radians(self, angle_degrees):
        return __import__("math").radians(angle_degrees)

    def _sin(self, angle):
        return __import__("math").sin(angle)

    def _cos(self, angle):
        return __import__("math").cos(angle)

    def _point_tuple(self, point):
        return (float(point.X), float(point.Y), float(point.Z))

    def _slot_width_axis(self, axis, direction):
        width_axis = self._cross(direction, axis)
        if self._length(width_axis) <= 1e-12:
            raise ValueError("slot_cut axis and direction must not be parallel.")
        return self._unit_vector(width_axis)

    def _axis_index(self, vector):
        values = [abs(value) for value in vector]
        index = values.index(max(values))
        if values[index] < 0.999:
            raise ValueError("This NXBuilder helper currently requires axis-aligned vectors.")
        return index

    def _slot_bridge_box(self, center, axis, direction, length, width, depth):
        width_axis = self._slot_width_axis(axis, direction)
        for vector in (axis, width_axis, direction):
            self._axis_index(vector)

        points = []
        for axis_sign in (-1.0, 1.0):
            for width_sign in (-1.0, 1.0):
                for depth_scale in (0.0, 1.0):
                    point = center
                    point = self._add_vectors(
                        point,
                        self._scale_vector(axis, axis_sign * float(length) / 2.0),
                    )
                    point = self._add_vectors(
                        point,
                        self._scale_vector(width_axis, width_sign * float(width) / 2.0),
                    )
                    point = self._add_vectors(
                        point,
                        self._scale_vector(direction, depth_scale * float(depth)),
                    )
                    points.append(point)

        mins = tuple(min(point[index] for point in points) for index in range(3))
        maxs = tuple(max(point[index] for point in points) for index in range(3))
        lengths = tuple(maxs[index] - mins[index] for index in range(3))
        return lengths, mins

    def _set_expression(self, expression, value):
        text_value = str(float(value))
        if hasattr(expression, "RightHandSide"):
            expression.RightHandSide = text_value
        else:
            expression.Value = float(value)

    def _external_component_not_implemented(self, operation, **details):
        detail_text = ", ".join(
            f"{key}={value!r}"
            for key, value in sorted(details.items())
            if value not in (None, {}, ())
        )
        suffix = f" Details: {detail_text}." if detail_text else ""
        return NotImplementedError(
            f"NXBuilder.{operation} requires official Siemens NXOpen import/component APIs "
            "and a real Siemens NX runtime validation pass before generated journals may "
            f"use external STEP components.{suffix}"
        )

    def _edges_on_z_extreme(self, body, highest=True, tolerance=1e-6):
        edges = list(body.GetEdges())
        edge_points = []
        z_values = []

        for edge in edges:
            points = self._edge_vertices(edge)
            if len(points) != 2:
                continue
            edge_points.append((edge, points))
            z_values.extend((points[0].Z, points[1].Z))

        if not z_values:
            return []

        target_z = max(z_values) if highest else min(z_values)
        selected = []
        for edge, points in edge_points:
            if all(abs(point.Z - target_z) <= tolerance for point in points):
                selected.append(edge)
        return selected

    def _edge_vertices(self, edge):
        vertices = edge.GetVertices()
        if isinstance(vertices, tuple):
            return vertices
        if isinstance(vertices, list):
            return vertices
        return list(vertices)

    def _builder_member(self, builder, name):
        member = getattr(builder, name)
        return member() if callable(member) else member

    def _enum_value(self, enum_class, *names):
        if enum_class is None:
            return None
        for name in names:
            if hasattr(enum_class, name):
                return getattr(enum_class, name)
        return None

    def _set_boolean_bodies(self, builder, target_body, tool_body):
        if hasattr(builder, "Target"):
            builder.Target = target_body
        elif hasattr(builder, "TargetBodyCollector"):
            builder.TargetBodyCollector.Add(target_body)
        elif hasattr(builder, "Targets"):
            builder.Targets.Add(target_body)
        else:
            raise RuntimeError("NX BooleanBuilder has no target body input.")

        if hasattr(builder, "Tool"):
            builder.Tool = tool_body
        elif hasattr(builder, "ToolBodyCollector"):
            builder.ToolBodyCollector.Add(tool_body)
        elif hasattr(builder, "Tools"):
            builder.Tools.Add(tool_body)
        else:
            raise RuntimeError("NX BooleanBuilder has no tool body input.")

    def _add_edge_blend_chainset(self, builder, edges, radius_text):
        collector = self.part.ScCollectors.CreateCollector()
        rule = self.part.ScRuleFactory.CreateRuleEdgeDumb(edges)
        collector.ReplaceRules([rule], False)

        add_chainset = getattr(builder, "AddChainset", None)
        if add_chainset is None:
            add_chainset = getattr(builder, "AddChainSet", None)
        if add_chainset is None:
            raise AttributeError(
                "EdgeBlendBuilder has neither AddConstantRadiusEdge nor AddChainset"
            )

        add_chainset(collector, radius_text)

    def _set_chamfer_edges(self, builder, edges):
        collector = self.part.ScCollectors.CreateCollector()
        rule = self.part.ScRuleFactory.CreateRuleEdgeDumb(edges)
        collector.ReplaceRules([rule], False)

        if hasattr(builder, "SmartCollector"):
            smart_collector = getattr(builder, "SmartCollector")
            if smart_collector is None:
                try:
                    builder.SmartCollector = collector
                    return
                except Exception:
                    pass
            elif hasattr(smart_collector, "ReplaceRules"):
                smart_collector.ReplaceRules([rule], False)
                return
            elif hasattr(smart_collector, "Add"):
                for edge in edges:
                    smart_collector.Add(edge)
                return
            else:
                try:
                    builder.SmartCollector = collector
                    return
                except Exception:
                    pass

        if hasattr(builder, "Collector"):
            builder.Collector = collector
            return

        if hasattr(builder, "ScCollector"):
            builder.ScCollector = collector
            return

        raise AttributeError("ChamferBuilder has no supported edge collector input")

    def _create_step_exporter(self):
        dex_manager = self.session.DexManager
        if hasattr(dex_manager, "CreateStepCreator"):
            return dex_manager.CreateStepCreator()
        if hasattr(dex_manager, "CreateStep214Creator"):
            return dex_manager.CreateStep214Creator()
        raise RuntimeError("NX DexManager has no STEP export creator.")

    def _create_step214_importer(self):
        dex_manager = self.session.DexManager
        if hasattr(dex_manager, "CreateStep214Importer"):
            return dex_manager.CreateStep214Importer()
        raise RuntimeError("NX DexManager has no STEP214 import creator.")

    def _call_or_set(self, obj, name, value):
        member = getattr(obj, name, None)
        if callable(member):
            member(value)
            return
        if hasattr(obj, name):
            setattr(obj, name, value)
            return
        raise AttributeError(f"{obj.__class__.__name__} has no {name} setter")

    def _is_generic_step_creator(self, exporter):
        creator_class = getattr(NXOpen, exporter.__class__.__name__, None)
        return (
            creator_class is getattr(NXOpen, "StepCreator", None)
            or hasattr(exporter, "ExportFrom")
        )

    def _set_export_from_display_part(self, exporter):
        creator_class = getattr(NXOpen, exporter.__class__.__name__, None)
        enum_class = getattr(creator_class, "ExportFromOption", None)
        display_part = self._enum_value(enum_class, "DisplayPart")
        if display_part is not None and hasattr(exporter, "ExportFrom"):
            exporter.ExportFrom = display_part

    def _set_step_export_as_ap242(self, exporter):
        creator_class = getattr(NXOpen, exporter.__class__.__name__, None)
        enum_class = getattr(creator_class, "ExportAsOption", None)
        ap242 = self._enum_value(enum_class, "Ap242")
        if ap242 is not None and hasattr(exporter, "ExportAs"):
            exporter.ExportAs = ap242

    def _enable_step_solid_export(self, exporter):
        object_types = getattr(exporter, "ObjectTypes", None)
        if object_types is None or not hasattr(object_types, "Solids"):
            raise AttributeError(
                "NX StepCreator has no ObjectTypes.Solids filter; "
                "cannot guarantee solid STEP export"
            )
        object_types.Solids = True

    def _set_step_export_as_ap214(self, exporter):
        creator_class = getattr(NXOpen, exporter.__class__.__name__, None)
        enum_class = getattr(creator_class, "ExportAsOption", None)
        ap214 = self._enum_value(enum_class, "Ap214")
        if ap214 is not None and hasattr(exporter, "ExportAs"):
            exporter.ExportAs = ap214

    def _set_export_destination_to_file(self, exporter):
        enum_class = getattr(NXOpen.BaseCreator, "ExportDestinationOption", None)
        native_file_system = self._enum_value(enum_class, "NativeFileSystem")
        if native_file_system is not None and hasattr(exporter, "ExportDestination"):
            exporter.ExportDestination = native_file_system

    def _set_optional_attr(self, obj, name, value):
        if hasattr(obj, name):
            setattr(obj, name, value)

    def _ensure_saved_part_for_export(self, output_path):
        part_path = getattr(self.part, "FullPath", "") or ""
        if part_path and os.path.exists(part_path):
            return part_path

        root, _ = os.path.splitext(output_path)
        candidates = [root + ".prt"]

        script_path = self._caller_script_path()
        if script_path:
            work_dir = os.path.join(os.path.dirname(script_path), "_cadnx_work")
            candidates.append(os.path.join(work_dir, os.path.basename(root) + ".prt"))

        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            os.makedirs(os.path.dirname(candidate), exist_ok=True)
            try:
                save_status = self.part.SaveAs(candidate)
                if save_status is not None:
                    save_status.Dispose()
                if os.path.exists(candidate):
                    return candidate
                print(
                    "WARNING: NX SaveAs finished but the PRT file was not found: "
                    f"{candidate}"
                )
            except Exception as exc:
                print(f"WARNING: NX SaveAs failed for {candidate}: {exc}")

        print(
            "WARNING: exporting STEP from the display part without a saved PRT input. "
            "If STEP export fails, reduce fragile features or run NX part checks."
        )
        return ""

    def _resolve_step_output_path(self, output_path):
        output_path = str(output_path)
        script_path = self._caller_script_path()

        if self._is_placeholder_step_name(output_path):
            if script_path:
                output_path = os.path.splitext(script_path)[0] + ".step"
            else:
                output_path = os.path.join(os.getcwd(), "cadnx_export.step")

        if os.path.basename(output_path).lower() == "output.step" and script_path:
            output_path = os.path.splitext(script_path)[0] + ".step"

        root, ext = os.path.splitext(output_path)
        if not ext:
            output_path = root + ".step"

        if os.path.isabs(output_path):
            return output_path

        base_dir = os.path.dirname(script_path) if script_path else ""
        if not base_dir:
            part_path = getattr(self.part, "FullPath", "") if self.part is not None else ""
            part_dir = os.path.dirname(part_path)
            if os.path.basename(part_dir).lower() != "_cadnx_work":
                base_dir = part_dir
        if not base_dir:
            base_dir = os.getcwd()
        return os.path.abspath(os.path.join(base_dir, output_path))

    def _is_placeholder_step_name(self, output_path):
        normalized = output_path.replace("\\", "/").strip()
        name = os.path.basename(normalized).lower()
        return name in ("", ".step", "output.step")

    def _recover_step_output(self, output_path):
        output_dir = os.path.dirname(output_path)
        if not output_dir or not os.path.isdir(output_dir):
            return ""

        step_files = []
        for name in os.listdir(output_dir):
            candidate = os.path.join(output_dir, name)
            if os.path.isfile(candidate) and name.lower().endswith((".stp", ".step")):
                step_files.append(candidate)
        if not step_files:
            return ""

        newest = max(step_files, key=lambda path: os.path.getmtime(path))
        if os.path.abspath(newest) == os.path.abspath(output_path):
            return newest
        os.replace(newest, output_path)
        return newest

    def _caller_script_path(self):
        builder_path = os.path.abspath(__file__)
        for frame in inspect.stack():
            filename = os.path.abspath(frame.filename)
            if filename == builder_path:
                continue
            if os.path.basename(filename).lower() == "builder.py":
                continue
            if filename.endswith(".py") and os.path.exists(filename):
                return filename
        script_path = sys.argv[0] if sys.argv else ""
        if script_path and script_path.endswith(".py") and os.path.exists(script_path):
            return os.path.abspath(script_path)
        return ""

    def _create_work_part(self, part_name=None):
        """Create a millimeter work part when the NX session has no active part."""
        part_name = part_name or self._new_part_name()
        if os.path.exists(part_name) or os.path.exists(part_name + ".prt"):
            raise RuntimeError("Refusing to overwrite existing NX part: " + part_name)
        result = self.session.Parts.NewDisplay(
            part_name,
            NXOpen.Part.Units.Millimeters,
        )

        load_status = None
        if isinstance(result, tuple):
            part = result[0]
            if len(result) > 1:
                load_status = result[1]
        else:
            part = result

        if load_status is not None:
            load_status.Dispose()

        work_part = self.session.Parts.Work or part
        if work_part is None:
            raise RuntimeError(
                "NXBuilder could not create a work part. "
                "Open or create a part in NX, then run the generated script again."
            )
        return work_part

    def _new_part_name(self):
        script_path = self._caller_script_path()
        base = os.path.splitext(os.path.basename(script_path))[0] or "cadnx_generated_part"
        base = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in base)
        base = base[:80] or "cadnx_generated_part"
        base_dir = os.path.dirname(os.path.abspath(script_path)) if script_path else os.getcwd()
        work_dir = os.path.join(base_dir, "_cadnx_work")
        os.makedirs(work_dir, exist_ok=True)
        pid = os.getpid()
        candidate = os.path.join(work_dir, f"{base}_{pid}")
        for index in range(1, 1000):
            path = candidate if index == 1 else f"{candidate}_{index}"
            if not os.path.exists(path + ".prt"):
                return path
        raise RuntimeError("Could not create a unique NX part name.")

    def _body(self, feature):
        """Extract the first NXOpen.Body from a feature, or pass through if already a Body."""
        if isinstance(feature, NXOpen.Body):
            return feature
        bodies = feature.GetBodies()
        if not bodies:
            raise ValueError(f"Feature has no bodies: {feature}")
        return bodies[0]
