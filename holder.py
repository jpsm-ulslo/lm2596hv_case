import cadquery as cq

from geometry import (
    create_geometry,
    merge_config,
)


# ============================================================
# CREATE HOLDER SHELL
# ============================================================

def create_holder_shell(geometry):

    cx = geometry["center"]["x"]
    cy = geometry["center"]["y"]

    width = geometry["outer"]["width"]
    depth = geometry["outer"]["depth"]

    corner_radius = (
        geometry["outer"]["corner_radius"]
    )

    base_thickness = (
        geometry["holder"]["base_thickness"]
    )

    wall_thickness = (
        geometry["holder"]["wall_thickness"]
    )

    wall_height = (
        geometry["holder"]["wall_height"]
    )

    # --------------------------------------------------------
    # Outer body
    # --------------------------------------------------------

    outer = (

        cq.Workplane("XY")

        .center(cx, cy)

        .rect(
            width,
            depth
        )

        .extrude(
            base_thickness
            + wall_height
        )

        .edges("|Z")

        .fillet(
            corner_radius
        )
    )

    # --------------------------------------------------------
    # Internal cavity
    # --------------------------------------------------------

    inner_width = (
        geometry["inner"]["width"]
    )

    inner_depth = (
        geometry["inner"]["depth"]
    )

    inner = (

        cq.Workplane("XY")

        .center(cx, cy)

        .workplane(
            offset=base_thickness
        )

        .rect(
            inner_width,
            inner_depth
        )

        .extrude(
            wall_height + 1.0
        )
    )

    holder = outer.cut(inner)

    # Cut matching half-cylinder grooves into both long inner walls.
    snap = geometry["snap"]

    if snap["enabled"]:

        snap_length = snap["length"]
        snap_short_length = snap["short_length"]
        snap_z = snap["z"]
        snap_y = cy - snap_length / 2

        groove = cq.Workplane("XY")

        for snap_x in (
            cx - inner_width / 2,
            cx + inner_width / 2,
        ):

            cutter = cq.Solid.makeCylinder(
                snap["groove_radius"],
                snap_length,
                cq.Vector(snap_x, snap_y, snap_z),
                cq.Vector(0, 1, 0),
            )

            groove = groove.union(
                cq.Workplane("XY").newObject([cutter])
            )

        snap_x = cx - snap_short_length / 2

        for snap_y in (
            cy - inner_depth / 2,
            cy + inner_depth / 2,
        ):

            cutter = cq.Solid.makeCylinder(
                snap["groove_radius"],
                snap_short_length,
                cq.Vector(snap_x, snap_y, snap_z),
                cq.Vector(1, 0, 0),
            )

            groove = groove.union(
                cq.Workplane("XY").newObject([cutter])
            )

        holder = holder.cut(groove)

    # Optional hardcoded test openings on the +X long wall.
    side_holes = geometry["config"]

    if side_holes["make_side_holes"]:

        hole_width = side_holes["side_hole_width"]
        hole_height = (
            side_holes["side_hole_top_z"]
            - side_holes["side_hole_bottom_z"]
        )
        corner_radius = min(
            side_holes["side_hole_corner_radius"],
            hole_width / 2,
            hole_height / 2,
        )
        hole_spacing = side_holes["side_hole_spacing"]
        hole_center_x = (
            cx
            + width / 2
            - wall_thickness / 2
        )
        hole_offset_y = (
            hole_width / 2
            + hole_spacing / 2
        )

        openings = cq.Workplane("XY")

        for hole_center_y in (
            cy - hole_offset_y,
            cy + hole_offset_y,
        ):

            opening = (
                cq.Workplane("YZ")
                .center(
                    hole_center_y,
                    side_holes["side_hole_bottom_z"]
                    + hole_height / 2
                )
                .box(
                    hole_width,
                    hole_height,
                    wall_thickness + 2.0,
                    centered=(True, True, False)
                )
                .edges("|X")
                .fillet(
                    corner_radius
                )
                .translate(
                    (
                        hole_center_x
                        - (wall_thickness + 2.0) / 2,
                        0,
                        0
                    )
                )
            )

            openings = openings.union(opening)

        holder = holder.cut(openings)

    return holder


# ============================================================
# ADD MOUNTING PEGS
# ============================================================

def add_mounting_pegs(
    holder,
    geometry
):

    cfg = geometry["config"]

    holes = (
        geometry["mounting"]["holes"]
    )

    base_thickness = (
        geometry["holder"]["base_thickness"]
    )

    for x, y, radius in holes:

        hole_diameter = (
            2 * radius
        )

        peg_diameter = max(
            cfg["min_peg_diameter"],
            hole_diameter
            - 2 * cfg["peg_clearance"]
        )

        peg = (

            cq.Workplane("XY")

            .center(x, y)

            .circle(
                peg_diameter / 2
            )

            .extrude(
                cfg["peg_height"]
            )
        )

        # ----------------------------------------------------
        # Chamfer peg top
        # ----------------------------------------------------

        if cfg["peg_chamfer"] > 0:

            peg = (
                peg
                .faces(">Z")
                .chamfer(
                    cfg["peg_chamfer"]
                )
            )

        peg = peg.translate(
            (
                0,
                0,
                base_thickness
            )
        )

        holder = holder.union(peg)

    return holder


# ============================================================
# MAIN HOLDER
# ============================================================

def create_holder(
    contour,
    holes,
    config=None
):

    cfg = merge_config(config)

    # --------------------------------------------------------
    # Shared geometry
    # --------------------------------------------------------

    geometry = create_geometry(
        contour,
        holes,
        cfg
    )

    # --------------------------------------------------------
    # Shell
    # --------------------------------------------------------

    holder = create_holder_shell(
        geometry
    )

    # --------------------------------------------------------
    # Mounting pegs
    # --------------------------------------------------------

    holder = add_mounting_pegs(
        holder,
        geometry
    )

    return holder, geometry