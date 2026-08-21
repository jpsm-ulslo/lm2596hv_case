from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any


# ============================================================
# SHARED DEFAULT CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {

    # --------------------------------------------------------
    # Holder base
    # --------------------------------------------------------

    "base_thickness": 2.4,
    "base_margin": 5.0,
    "base_corner_radius": 4.0,

    # --------------------------------------------------------
    # Holder walls
    # --------------------------------------------------------

    "wall_thickness": 2.0,
    "wall_height": 25.0,

    # --------------------------------------------------------
    # Mounting pegs
    # --------------------------------------------------------

    "peg_height": 5.0,
    "peg_clearance": 0.30,
    "min_peg_diameter": 1.6,
    "peg_chamfer": 0.6,

    # --------------------------------------------------------
    # Lid
    # --------------------------------------------------------

    "lid_thickness": 2.0,
    "lid_overhang": 1.0,

    # Clearance between skirt and holder
    "lid_clearance": 0.30,

    # Skirt
    "skirt_height": 6.0,
    "skirt_thickness": 1.5,

    # Lid corner radius
    "lid_corner_radius": 3.0,

    # Lid top edge fillet
    "lid_top_fillet": 0.5,
}


# ============================================================
# CONFIGURATION
# ============================================================

def merge_config(config=None):

    cfg = {
        **DEFAULT_CONFIG
    }

    if config:
        cfg.update(config)

    return cfg


# ============================================================
# CONTOUR BOUNDS
# ============================================================

def contour_bounds(contour):

    xmin = contour[:, 0].min()
    ymin = contour[:, 1].min()

    xmax = contour[:, 0].max()
    ymax = contour[:, 1].max()

    return xmin, ymin, xmax, ymax


# ============================================================
# CREATE SHARED GEOMETRY
# ============================================================

def create_geometry(
    contour,
    holes,
    config=None
):
    """
    Create the common geometry contract.

    This object is shared between:

        holder.py
        lid.py
        future enclosure modules
    """

    cfg = merge_config(config)

    xmin, ymin, xmax, ymax = contour_bounds(contour)

    # --------------------------------------------------------
    # PCB
    # --------------------------------------------------------

    pcb_width = xmax - xmin
    pcb_depth = ymax - ymin

    pcb_center_x = (xmin + xmax) / 2
    pcb_center_y = (ymin + ymax) / 2

    # --------------------------------------------------------
    # Holder outer envelope
    # --------------------------------------------------------

    outer_min_x = xmin - cfg["base_margin"]
    outer_max_x = xmax + cfg["base_margin"]

    outer_min_y = ymin - cfg["base_margin"]
    outer_max_y = ymax + cfg["base_margin"]

    outer_width = outer_max_x - outer_min_x
    outer_depth = outer_max_y - outer_min_y

    outer_center_x = (
        outer_min_x + outer_max_x
    ) / 2

    outer_center_y = (
        outer_min_y + outer_max_y
    ) / 2

    # --------------------------------------------------------
    # Holder inner cavity
    # --------------------------------------------------------

    inner_width = (
        outer_width
        - 2 * cfg["wall_thickness"]
    )

    inner_depth = (
        outer_depth
        - 2 * cfg["wall_thickness"]
    )

    # --------------------------------------------------------
    # Z reference planes
    # --------------------------------------------------------

    base_bottom_z = 0.0

    base_top_z = (
        base_bottom_z
        + cfg["base_thickness"]
    )

    wall_top_z = (
        base_top_z
        + cfg["wall_height"]
    )

    # --------------------------------------------------------
    # Lid
    # --------------------------------------------------------

    lid_bottom_z = wall_top_z

    lid_top_z = (
        lid_bottom_z
        + cfg["lid_thickness"]
    )

    # --------------------------------------------------------
    # Lid skirt
    #
    # Skirt fits inside holder cavity.
    # Clearance is applied on each side.
    # --------------------------------------------------------

    skirt_outer_width = (
        inner_width
        - 2 * cfg["lid_clearance"]
    )

    skirt_outer_depth = (
        inner_depth
        - 2 * cfg["lid_clearance"]
    )

    skirt_inner_width = (
        skirt_outer_width
        - 2 * cfg["skirt_thickness"]
    )

    skirt_inner_depth = (
        skirt_outer_depth
        - 2 * cfg["skirt_thickness"]
    )

    skirt_top_z = lid_bottom_z

    skirt_bottom_z = (
        skirt_top_z
        - cfg["skirt_height"]
    )

    # --------------------------------------------------------
    # Lid external dimensions
    # --------------------------------------------------------

    lid_width = (
        outer_width
        + 2 * cfg["lid_overhang"]
    )

    lid_depth = (
        outer_depth
        + 2 * cfg["lid_overhang"]
    )

    # --------------------------------------------------------
    # Validate dimensions
    # --------------------------------------------------------

    if inner_width <= 0:
        raise ValueError(
            "Holder inner width <= 0."
        )

    if inner_depth <= 0:
        raise ValueError(
            "Holder inner depth <= 0."
        )

    if skirt_outer_width <= 0:
        raise ValueError(
            "Lid skirt outer width <= 0."
        )

    if skirt_outer_depth <= 0:
        raise ValueError(
            "Lid skirt outer depth <= 0."
        )

    if skirt_inner_width <= 0:
        raise ValueError(
            "Lid skirt inner width <= 0. "
            "Reduce skirt thickness."
        )

    if skirt_inner_depth <= 0:
        raise ValueError(
            "Lid skirt inner depth <= 0. "
            "Reduce skirt thickness."
        )

    # --------------------------------------------------------
    # Shared geometry contract
    # --------------------------------------------------------

    geometry = {

        # ====================================================
        # CONFIG
        # ====================================================

        "config": cfg,

        # ====================================================
        # GLOBAL CENTER
        # ====================================================

        "center": {
            "x": outer_center_x,
            "y": outer_center_y,
        },

        # ====================================================
        # PCB
        # ====================================================

        "pcb": {

            "bounds": {
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
            },

            "width": pcb_width,
            "depth": pcb_depth,

            "center": {
                "x": pcb_center_x,
                "y": pcb_center_y,
            },
        },

        # ====================================================
        # HOLDER OUTER
        # ====================================================

        "outer": {

            "bounds": {
                "xmin": outer_min_x,
                "ymin": outer_min_y,
                "xmax": outer_max_x,
                "ymax": outer_max_y,
            },

            "width": outer_width,
            "depth": outer_depth,

            "center": {
                "x": outer_center_x,
                "y": outer_center_y,
            },

            "corner_radius":
                cfg["base_corner_radius"],
        },

        # ====================================================
        # HOLDER INNER
        # ====================================================

        "inner": {

            "width": inner_width,
            "depth": inner_depth,

            "center": {
                "x": outer_center_x,
                "y": outer_center_y,
            },

            "corner_radius": max(
                0,
                cfg["base_corner_radius"]
                - cfg["wall_thickness"]
            ),
        },

        # ====================================================
        # HOLDER
        # ====================================================

        "holder": {

            "base_thickness":
                cfg["base_thickness"],

            "wall_thickness":
                cfg["wall_thickness"],

            "wall_height":
                cfg["wall_height"],

            "corner_radius":
                cfg["base_corner_radius"],
        },

        # ====================================================
        # LID
        # ====================================================

        "lid": {

            "width": lid_width,
            "depth": lid_depth,

            "thickness":
                cfg["lid_thickness"],

            "overhang":
                cfg["lid_overhang"],

            "corner_radius":
                cfg["lid_corner_radius"],

            "top_fillet":
                cfg["lid_top_fillet"],

            "center": {
                "x": outer_center_x,
                "y": outer_center_y,
            },
        },

        # ====================================================
        # SKIRT
        # ====================================================

        "skirt": {

            "outer_width":
                skirt_outer_width,

            "outer_depth":
                skirt_outer_depth,

            "inner_width":
                skirt_inner_width,

            "inner_depth":
                skirt_inner_depth,

            "thickness":
                cfg["skirt_thickness"],

            "height":
                cfg["skirt_height"],

            "clearance":
                cfg["lid_clearance"],

            "corner_radius":
                max(
                    0,
                    cfg["base_corner_radius"]
                    - cfg["wall_thickness"]
                ),
        },

        # ====================================================
        # Z PLANES
        # ====================================================

        "z": {

            "base_bottom":
                base_bottom_z,

            "base_top":
                base_top_z,

            "wall_top":
                wall_top_z,

            "lid_bottom":
                lid_bottom_z,

            "lid_top":
                lid_top_z,

            "skirt_bottom":
                skirt_bottom_z,

            "skirt_top":
                skirt_top_z,
        },

        # ====================================================
        # MOUNTING
        # ====================================================

        "mounting": {

            "holes": holes,

            "peg_height":
                cfg["peg_height"],

            "peg_clearance":
                cfg["peg_clearance"],
        },
    }

    return geometry