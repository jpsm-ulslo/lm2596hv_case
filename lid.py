import cadquery as cq


# ============================================================
# CREATE LID
# ============================================================

def create_lid(
    geometry,
    config=None
):
    """
    Create the complete lid from the shared geometry.

    The lid is positioned automatically relative to:

        geometry["z"]["wall_top"]

    The skirt enters the holder cavity.
    """

    cfg = {
        **geometry["config"],
        **(config or {})
    }

    # --------------------------------------------------------
    # Top
    # --------------------------------------------------------

    lid = create_lid_top(
        geometry,
        cfg
    )

    # --------------------------------------------------------
    # Internal skirt
    # --------------------------------------------------------

    skirt = create_lid_skirt(
        geometry,
        cfg
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    lid = lid.union(skirt)

    return lid


# ============================================================
# LID TOP
# ============================================================

def create_lid_top(
    geometry,
    config
):

    cx = geometry["center"]["x"]
    cy = geometry["center"]["y"]

    width = geometry["lid"]["width"]
    depth = geometry["lid"]["depth"]

    corner_radius = (
        geometry["lid"]["corner_radius"]
    )

    lid_thickness = (
        geometry["lid"]["thickness"]
    )

    lid_bottom_z = (
        geometry["z"]["lid_bottom"]
    )

    lid = (

        cq.Workplane("XY")

        .center(
            cx,
            cy
        )

        .rect(
            width,
            depth
        )

        .extrude(
            lid_thickness
        )

        .edges("|Z")

        .fillet(
            corner_radius
        )
    )

    # --------------------------------------------------------
    # Move to top of holder
    # --------------------------------------------------------

    lid = lid.translate(
        (
            0,
            0,
            lid_bottom_z
        )
    )

    # --------------------------------------------------------
    # Optional top edge softening
    # --------------------------------------------------------

    top_fillet = (
        geometry["lid"]["top_fillet"]
    )

    if top_fillet > 0:

        try:

            lid = (

                lid

                .edges(">Z")

                .fillet(
                    top_fillet
                )
            )

        except Exception:

            # Keep lid valid even if
            # the requested fillet is
            # incompatible with geometry.
            pass

    return lid


# ============================================================
# LID SKIRT
# ============================================================

def create_lid_skirt(
    geometry,
    config
):

    cx = geometry["center"]["x"]
    cy = geometry["center"]["y"]

    outer_width = (
        geometry["skirt"]["outer_width"]
    )

    outer_depth = (
        geometry["skirt"]["outer_depth"]
    )

    inner_width = (
        geometry["skirt"]["inner_width"]
    )

    inner_depth = (
        geometry["skirt"]["inner_depth"]
    )

    skirt_thickness = (
        geometry["skirt"]["thickness"]
    )

    skirt_height = (
        geometry["skirt"]["height"]
    )

    skirt_top_z = (
        geometry["z"]["skirt_top"]
    )

    skirt_bottom_z = (
        geometry["z"]["skirt_bottom"]
    )

    # --------------------------------------------------------
    # Skirt corner radius
    # --------------------------------------------------------

    corner_radius = (
        geometry["skirt"]["corner_radius"]
    )

    # --------------------------------------------------------
    # Outer skirt
    # --------------------------------------------------------

    outer = (

        cq.Workplane("XY")

        .center(
            cx,
            cy
        )

        .rect(
            outer_width,
            outer_depth
        )

        .extrude(
            skirt_height
        )
    )

    if corner_radius > 0:

        outer = (

            outer

            .edges("|Z")

            .fillet(
                corner_radius
            )
        )

    # --------------------------------------------------------
    # Inner cavity of skirt
    # --------------------------------------------------------

    inner = (

        cq.Workplane("XY")

        .center(
            cx,
            cy
        )

        .rect(
            inner_width,
            inner_depth
        )

        .extrude(
            skirt_height + 0.2
        )
    )

    if corner_radius > 0:

        inner_radius = max(
            0,
            corner_radius
            - skirt_thickness
        )

        if inner_radius > 0:

            inner = (

                inner

                .edges("|Z")

                .fillet(
                    inner_radius
                )
            )

    # --------------------------------------------------------
    # Hollow skirt
    # --------------------------------------------------------

    skirt = outer.cut(inner)

    # Add matching half-cylinder beads to both long sides.
    snap = geometry["snap"]

    if snap["enabled"]:

        snap_radius = snap["radius"]
        snap_length = snap["length"]
        snap_z = snap["z"] - skirt_bottom_z

        snap_y = cy - snap_length / 2

        for snap_x in (
            cx - outer_width / 2,
            cx + outer_width / 2,
        ):

            bead = cq.Solid.makeCylinder(
                snap_radius,
                snap_length,
                cq.Vector(snap_x, snap_y, snap_z),
                cq.Vector(0, 1, 0),
            )

            skirt = skirt.union(
                cq.Workplane("XY").newObject([bead])
            )

    # --------------------------------------------------------
    # Position below lid
    # --------------------------------------------------------

    skirt = skirt.translate(
        (
            0,
            0,
            skirt_bottom_z
        )
    )

    return skirt