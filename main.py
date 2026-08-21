import sys
import os

import cadquery as cq

from functions import (
    load_mesh,
    pcb_points,
    contour,
    find_mounting_holes,
)

from holder import (
    create_holder,
)

from lid import (
    create_lid,
)

from visualization import (
    visualize,
)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {

    # --------------------------------------------------------
    # Holder
    # --------------------------------------------------------

    "base_thickness": 2.4,
    "base_margin": 5.0,
    "base_corner_radius": 4.0,

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

    "lid_clearance": 0.30,

    "skirt_height": 6.0,
    "skirt_thickness": 1.5,

    "lid_corner_radius": 3.0,
    "lid_top_fillet": 0.5,
}


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = "output"


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

def create_output_directory():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


# ============================================================
# EXPORT
# ============================================================

def export_models(
    holder,
    lid
):

    holder_file = os.path.join(
        OUTPUT_DIR,
        "holder.stl"
    )

    lid_file = os.path.join(
        OUTPUT_DIR,
        "lid.stl"
    )

    cq.exporters.export(
        holder,
        holder_file
    )

    cq.exporters.export(
        lid,
        lid_file
    )

    print()
    print("Generated:")

    print(
        f"  {holder_file}"
    )

    print(
        f"  {lid_file}"
    )


# ============================================================
# PRINT GEOMETRY INFORMATION
# ============================================================

def print_geometry_summary(
    geometry,
    holes
):

    print()
    print("=" * 60)
    print("GEOMETRY")
    print("=" * 60)

    print()

    # --------------------------------------------------------
    # PCB
    # --------------------------------------------------------

    print("PCB")

    print(
        f"  Width:  "
        f"{geometry['pcb']['width']:.2f} mm"
    )

    print(
        f"  Depth:  "
        f"{geometry['pcb']['depth']:.2f} mm"
    )

    print()

    # --------------------------------------------------------
    # Holder
    # --------------------------------------------------------

    print("HOLDER")

    print(
        f"  Width:  "
        f"{geometry['outer']['width']:.2f} mm"
    )

    print(
        f"  Depth:  "
        f"{geometry['outer']['depth']:.2f} mm"
    )

    print(
        f"  Base:   "
        f"{geometry['holder']['base_thickness']:.2f} mm"
    )

    print(
        f"  Walls:  "
        f"{geometry['holder']['wall_thickness']:.2f} mm"
    )

    print(
        f"  Height: "
        f"{geometry['holder']['wall_height']:.2f} mm"
    )

    print()

    # --------------------------------------------------------
    # Lid
    # --------------------------------------------------------

    print("LID")

    print(
        f"  Width:  "
        f"{geometry['lid']['width']:.2f} mm"
    )

    print(
        f"  Depth:  "
        f"{geometry['lid']['depth']:.2f} mm"
    )

    print(
        f"  Thickness: "
        f"{geometry['lid']['thickness']:.2f} mm"
    )

    print()

    # --------------------------------------------------------
    # Skirt
    # --------------------------------------------------------

    print("LID SKIRT")

    print(
        f"  Outer width: "
        f"{geometry['skirt']['outer_width']:.2f} mm"
    )

    print(
        f"  Outer depth: "
        f"{geometry['skirt']['outer_depth']:.2f} mm"
    )

    print(
        f"  Thickness:   "
        f"{geometry['skirt']['thickness']:.2f} mm"
    )

    print(
        f"  Height:      "
        f"{geometry['skirt']['height']:.2f} mm"
    )

    print(
        f"  Clearance:   "
        f"{geometry['skirt']['clearance']:.2f} mm"
    )

    print()

    # --------------------------------------------------------
    # Z references
    # --------------------------------------------------------

    print("Z PLANES")

    print(
        f"  Base bottom: "
        f"{geometry['z']['base_bottom']:.2f} mm"
    )

    print(
        f"  Base top:    "
        f"{geometry['z']['base_top']:.2f} mm"
    )

    print(
        f"  Wall top:    "
        f"{geometry['z']['wall_top']:.2f} mm"
    )

    print(
        f"  Skirt bottom:"
        f" {geometry['z']['skirt_bottom']:.2f} mm"
    )

    print(
        f"  Skirt top:   "
        f"{geometry['z']['skirt_top']:.2f} mm"
    )

    print(
        f"  Lid bottom:  "
        f"{geometry['z']['lid_bottom']:.2f} mm"
    )

    print(
        f"  Lid top:     "
        f"{geometry['z']['lid_top']:.2f} mm"
    )

    print()

    # --------------------------------------------------------
    # Mounting holes
    # --------------------------------------------------------

    print("MOUNTING HOLES")

    print(
        f"  Detected: {len(holes)}"
    )

    for index, hole in enumerate(
        holes,
        start=1
    ):

        x, y, radius = hole

        print(
            f"  Hole {index}: "
            f"X={x:.2f} "
            f"Y={y:.2f} "
            f"Ø={2 * radius:.2f} mm"
        )

    print()

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # ARGUMENTS
    # ========================================================

    if len(sys.argv) < 2:

        raise SystemExit(
            "\nUsage:\n"
            "  python main.py <model.step>\n"
        )

    model_file = sys.argv[1]

    if not os.path.isfile(model_file):

        raise FileNotFoundError(
            f"STEP file not found:\n"
            f"{model_file}"
        )

    print()
    print("=" * 60)
    print("PCB ENCLOSURE GENERATOR")
    print("=" * 60)

    print()

    print(
        f"Input:\n"
        f"  {model_file}"
    )

    # ========================================================
    # LOAD STEP
    # ========================================================

    print()
    print("Loading STEP...")

    mesh = load_mesh(
        model_file
    )

    # ========================================================
    # NORMALIZE ORIENTATION
    # ========================================================

    print(
        "Normalizing orientation..."
    )

    mesh.rotate_z(
        90,
        inplace=True
    )

    mesh.rotate_y(
        90,
        inplace=True
    )

    # ========================================================
    # PCB EXTRACTION
    # ========================================================

    print(
        "Extracting PCB layer..."
    )

    pcb = pcb_points(
        mesh
    )

    if pcb is None or len(pcb) < 3:

        raise RuntimeError(
            "Could not extract a valid PCB layer."
        )

    print(
        f"  PCB points: {len(pcb)}"
    )

    # ========================================================
    # PCB CONTOUR
    # ========================================================

    print(
        "Calculating PCB contour..."
    )

    pcb_contour = contour(
        pcb
    )

    if pcb_contour is None:

        raise RuntimeError(
            "Could not calculate PCB contour."
        )

    # ========================================================
    # MOUNTING HOLES
    # ========================================================

    print(
        "Detecting mounting holes..."
    )

    pcb_xy = pcb[:, :2]

    holes = find_mounting_holes(
        pcb_xy,
        pcb_contour
    )

    print(
        f"Detected mounting holes: "
        f"{len(holes)}"
    )

    # ========================================================
    # CREATE HOLDER
    # ========================================================

    print()
    print(
        "Creating holder..."
    )

    holder, geometry = create_holder(
        contour=pcb_contour,
        holes=holes,
        config=CONFIG
    )

    # ========================================================
    # CREATE LID
    # ========================================================

    print(
        "Creating lid..."
    )

    lid = create_lid(
        geometry
    )

    # ========================================================
    # GEOMETRY SUMMARY
    # ========================================================

    print_geometry_summary(
        geometry,
        holes
    )

    # ========================================================
    # EXPORT
    # ========================================================

    print(
        "Exporting STL..."
    )

    create_output_directory()

    export_models(
        holder,
        lid
    )

    # ========================================================
    # VISUALIZATION
    # ========================================================

    print()
    print(
        "Opening visualization..."
    )

    visualize(
        holder=holder,
        lid=lid,
        geometry=geometry,
        pcb_mesh=mesh,
        mode="assembly",
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()