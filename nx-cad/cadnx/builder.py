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

    def __init__(self):
        if not _NX_AVAILABLE:
            raise RuntimeError(
                "NXOpen is not available. "
                "Run this file on a machine with Siemens NX installed "
                "via File -> Execute -> NX Open."
            )
        self.session = NXOpen.Session.GetSession()
        self.part = self.session.Parts.Work
        if self.part is None:
            self.part = self._create_work_part()

    # Primitives

    def box(self, length, width, height, origin=(0, 0, 0)):
        """Create a rectangular block. Returns Feature."""
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
            edge_axis = self._unit_vector(
                (
                    points[1].X - points[0].X,
                    points[1].Y - points[0].Y,
                    points[1].Z - points[0].Z,
                )
            )
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
        self._set_step_export_as_ap214(exporter)
        self._set_export_destination_to_file(exporter)
        if input_path:
            self._set_optional_attr(exporter, "InputFile", input_path)
        self._set_export_as_display_part(exporter)
        self._set_optional_attr(exporter, "OutputFile", output_path)
        self._set_optional_attr(exporter, "OutputFileExtension", "step")
        self._set_optional_attr(exporter, "FileSaveFlag", False)
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
        if hasattr(dex_manager, "CreateStep214Creator"):
            return dex_manager.CreateStep214Creator()
        if hasattr(dex_manager, "CreateStepCreator"):
            return dex_manager.CreateStepCreator()
        raise RuntimeError("NX DexManager has no STEP export creator.")

    def _set_export_as_display_part(self, exporter):
        export_as = getattr(exporter, "ExportAs", None)
        if export_as is None:
            return

        creator_class = getattr(NXOpen, exporter.__class__.__name__, None)
        enum_class = getattr(creator_class, "ExportAsOption", None)
        display_part = self._enum_value(enum_class, "DisplayPart")
        if display_part is not None:
            exporter.ExportAs = display_part

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

    def _create_work_part(self):
        """Create a millimeter work part when the NX session has no active part."""
        part_name = self._new_part_name()
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
