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