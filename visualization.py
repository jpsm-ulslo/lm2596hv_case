import cadquery as cq
import pyvista as pv


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {

    # --------------------------------------------------------
    # STEP / PCB
    # --------------------------------------------------------

    "show_pcb": True,

    "pcb_opacity": 1.0,

    # Automatically place STEP model on holder base
    "align_pcb": True,

    # --------------------------------------------------------
    # HOLDER
    # --------------------------------------------------------

    "show_holder": True,

    "holder_opacity": 0.35,

    # --------------------------------------------------------
    # LID
    # --------------------------------------------------------

    "show_lid": True,

    "lid_opacity": 0.30,

    # --------------------------------------------------------
    # EXPLODED VIEW
    # --------------------------------------------------------

    "exploded_distance": 15.0,

    # --------------------------------------------------------
    # SECTION
    # --------------------------------------------------------

    "enable_section": True,

    # --------------------------------------------------------
    # REFERENCE PLANES
    # --------------------------------------------------------

    "show_reference_planes": False,

    # --------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------

    "show_geometry_information": True,

    "show_fit_information": True,

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    "view": "isometric",

    # --------------------------------------------------------
    # MESH TESSELLATION
    # --------------------------------------------------------

    "tolerance": 0.05,
}


# ============================================================
# CADQUERY -> PYVISTA
# ============================================================

def cadquery_to_pyvista(
    solid,
    tolerance=0.05
):
    """
    Convert a CadQuery solid into a PyVista PolyData mesh.
    """

    shape = solid.val()

    vertices, triangles = shape.tessellate(
        tolerance
    )

    points = []

    for vertex in vertices:

        points.append(
            (
                float(vertex.x),
                float(vertex.y),
                float(vertex.z)
            )
        )

    faces = []

    for triangle in triangles:

        faces.extend(
            [
                3,
                int(triangle[0]),
                int(triangle[1]),
                int(triangle[2]),
            ]
        )

    return pv.PolyData(
        points,
        faces
    )


# ============================================================
# TRANSLATE MESH
# ============================================================

def translate_mesh(
    mesh,
    dx=0.0,
    dy=0.0,
    dz=0.0
):
    """
    Return a translated copy of a PyVista mesh.
    """

    result = mesh.copy()

    result.translate(
        (
            dx,
            dy,
            dz
        ),
        inplace=True
    )

    return result


# ============================================================
# GET MESH Z LIMITS
# ============================================================

def get_z_limits(
    mesh
):

    return (
        float(mesh.bounds[4]),
        float(mesh.bounds[5])
    )


# ============================================================
# ALIGN PCB / STEP
# ============================================================

def align_pcb_to_holder(
    pcb_mesh,
    geometry
):
    """
    Position the original STEP model so that its lowest point
    rests on top of the holder base.

    XY coordinates are deliberately NOT changed.

    The holder was generated from the STEP coordinates, so
    changing XY here would potentially destroy alignment
    between PCB and mounting pegs.
    """

    pcb_bottom = float(
        pcb_mesh.bounds[4]
    )

    base_top = float(
        geometry["z"]["base_top"]
    )

    dz = (
        base_top
        - pcb_bottom
    )

    return translate_mesh(
        pcb_mesh,
        dz=dz
    )


# ============================================================
# ALIGN LID - ASSEMBLED POSITION
# ============================================================

def align_lid_to_holder(
    lid_mesh,
    geometry
):
    """
    Position the lid in the CLOSED / FITTED position.

    The bottom of the lid mesh is the bottom of the skirt.
    We therefore place that bottom at:

        holder wall top - skirt height

    This makes the skirt extend down inside the holder.
    """

    wall_top = float(
        geometry["z"]["wall_top"]
    )

    skirt_height = float(
        geometry["skirt"]["height"]
    )

    current_bottom = float(
        lid_mesh.bounds[4]
    )

    target_bottom = (
        wall_top
        - skirt_height
    )

    dz = (
        target_bottom
        - current_bottom
    )

    return translate_mesh(
        lid_mesh,
        dz=dz
    )
# ============================================================
# CREATE ASSEMBLED LID
# ============================================================

def create_assembled_lid(
    lid_mesh,
    geometry
):
    """
    Return the lid in its physically assembled position.
    """

    return align_lid_to_holder(
        lid_mesh,
        geometry
    )


# ============================================================
# CREATE EXPLODED LID
# ============================================================

def create_exploded_lid(
    assembled_lid,
    distance
):
    """
    Exploded position is always calculated from the real
    assembled lid position.

    This prevents the lid from appearing to float or shift
    incorrectly.
    """

    return translate_mesh(
        assembled_lid,
        dz=distance
    )


# ============================================================
# Z INFORMATION
# ============================================================

def get_z_information(
    geometry
):

    z = geometry["z"]

    return {

        "base_bottom":
            float(z["base_bottom"]),

        "base_top":
            float(z["base_top"]),

        "wall_top":
            float(z["wall_top"]),

        "skirt_bottom":
            float(z["skirt_bottom"]),

        "skirt_top":
            float(z["skirt_top"]),

        "lid_bottom":
            float(z["lid_bottom"]),

        "lid_top":
            float(z["lid_top"]),
    }


# ============================================================
# FIT INFORMATION
# ============================================================

def calculate_fit_information(
    geometry
):
    """
    Calculate actual design clearance from the shared
    geometry.

    This is independent from the visualization.
    """

    inner_width = float(
        geometry["inner"]["width"]
    )

    inner_depth = float(
        geometry["inner"]["depth"]
    )

    skirt_width = float(
        geometry["skirt"]["outer_width"]
    )

    skirt_depth = float(
        geometry["skirt"]["outer_depth"]
    )

    width_total = (
        inner_width
        - skirt_width
    )

    depth_total = (
        inner_depth
        - skirt_depth
    )

    width_side = (
        width_total / 2.0
    )

    depth_side = (
        depth_total / 2.0
    )

    wall_top = float(
        geometry["z"]["wall_top"]
    )

    lid_bottom = float(
        geometry["z"]["lid_bottom"]
    )

    seating_error = (
        lid_bottom
        - wall_top
    )

    return {

        "holder_inner_width":
            inner_width,

        "holder_inner_depth":
            inner_depth,

        "skirt_outer_width":
            skirt_width,

        "skirt_outer_depth":
            skirt_depth,

        "width_clearance":
            width_side,

        "depth_clearance":
            depth_side,

        "wall_top":
            wall_top,

        "lid_bottom":
            lid_bottom,

        "seating_error":
            seating_error,
    }


# ============================================================
# FIT STATUS
# ============================================================

def fit_status(
    fit,
    tolerance=0.01
):
    """
    Determine whether the lid geometry is correctly seated.
    """

    width_ok = (
        fit["width_clearance"] >= 0
    )

    depth_ok = (
        fit["depth_clearance"] >= 0
    )

    seating_ok = (
        abs(
            fit["seating_error"]
        )
        <= tolerance
    )

    if (
        width_ok
        and depth_ok
        and seating_ok
    ):

        return "PASS"

    return "CHECK"


# ============================================================
# REFERENCE PLANE
# ============================================================

def create_reference_plane(
    geometry,
    z,
    scale=1.20
):

    width = (
        float(
            geometry["outer"]["width"]
        )
        * scale
    )

    depth = (
        float(
            geometry["outer"]["depth"]
        )
        * scale
    )

    center = geometry["center"]

    cx = float(
        center["x"]
    )

    cy = float(
        center["y"]
    )

    return pv.Plane(
        center=(
            cx,
            cy,
            z
        ),
        direction=(
            0,
            0,
            1
        ),
        i_size=width,
        j_size=depth
    )


# ============================================================
# ADD REFERENCE PLANES
# ============================================================

def add_reference_planes(
    plotter,
    geometry,
    z_info
):

    planes = {

        "base_top_plane":
            z_info["base_top"],

        "wall_top_plane":
            z_info["wall_top"],
    }

    for name, z in planes.items():

        plane = create_reference_plane(
            geometry,
            z
        )

        plotter.add_mesh(
            plane,
            name=name,
            opacity=0.08,
            show_edges=False
        )


# ============================================================
# GEOMETRY INFORMATION
# ============================================================

def build_geometry_text(
    geometry,
    z_info
):

    outer = geometry["outer"]

    holder = geometry["holder"]

    lid = geometry["lid"]

    skirt = geometry["skirt"]

    lines = [

        "GEOMETRY",

        "",

        "HOLDER",

        (
            f"  {outer['width']:.2f}"
            f" x "
            f"{outer['depth']:.2f} mm"
        ),

        (
            f"  Base: "
            f"{holder['base_thickness']:.2f} mm"
        ),

        (
            f"  Wall: "
            f"{holder['wall_thickness']:.2f} mm"
        ),

        (
            f"  Height: "
            f"{holder['wall_height']:.2f} mm"
        ),

        "",

        "LID",

        (
            f"  {lid['width']:.2f}"
            f" x "
            f"{lid['depth']:.2f} mm"
        ),

        (
            f"  Thickness: "
            f"{lid['thickness']:.2f} mm"
        ),

        "",

        "SKIRT",

        (
            f"  {skirt['outer_width']:.2f}"
            f" x "
            f"{skirt['outer_depth']:.2f} mm"
        ),

        (
            f"  Thickness: "
            f"{skirt['thickness']:.2f} mm"
        ),

        (
            f"  Height: "
            f"{skirt['height']:.2f} mm"
        ),

        "",

        "Z",

        (
            f"  Base top: "
            f"{z_info['base_top']:.2f}"
        ),

        (
            f"  Wall top: "
            f"{z_info['wall_top']:.2f}"
        ),

        (
            f"  Lid bottom: "
            f"{z_info['lid_bottom']:.2f}"
        ),

        (
            f"  Lid top: "
            f"{z_info['lid_top']:.2f}"
        ),
    ]

    return "\n".join(
        lines
    )


# ============================================================
# FIT INFORMATION
# ============================================================

def build_fit_text(
    fit
):

    status = fit_status(
        fit
    )

    lines = [

        "LID FIT CHECK",

        "",

        (
            f"Holder inner width : "
            f"{fit['holder_inner_width']:.2f} mm"
        ),

        (
            f"Skirt outer width  : "
            f"{fit['skirt_outer_width']:.2f} mm"
        ),

        (
            f"Clearance / side   : "
            f"{fit['width_clearance']:.2f} mm"
        ),

        "",

        (
            f"Holder inner depth : "
            f"{fit['holder_inner_depth']:.2f} mm"
        ),

        (
            f"Skirt outer depth  : "
            f"{fit['skirt_outer_depth']:.2f} mm"
        ),

        (
            f"Clearance / side   : "
            f"{fit['depth_clearance']:.2f} mm"
        ),

        "",

        (
            f"Wall top           : "
            f"{fit['wall_top']:.2f} mm"
        ),

        (
            f"Lid underside      : "
            f"{fit['lid_bottom']:.2f} mm"
        ),

        (
            f"Seating difference : "
            f"{fit['seating_error']:.3f} mm"
        ),

        "",

        f"STATUS: {status}",
    ]

    return "\n".join(
        lines
    )


# ============================================================
# ADD INFORMATION PANELS
# ============================================================

def add_information_panels(
    plotter,
    geometry,
    z_info,
    show_geometry=True,
    show_fit=True
):

    if show_geometry:

        geometry_text = build_geometry_text(
            geometry,
            z_info
        )

        plotter.add_text(
            geometry_text,
            name="geometry_information",
            position="upper_left",
            font_size=9
        )

    if show_fit:

        fit = calculate_fit_information(
            geometry
        )

        fit_text = build_fit_text(
            fit
        )

        plotter.add_text(
            fit_text,
            name="fit_information",
            position="lower_left",
            font_size=10
        )


# ============================================================
# SECTION ACTOR CLEANUP
# ============================================================

def remove_section_actors(
    plotter
):

    names = [

        "holder_section",

        "pcb_section",

        "lid_section",

        "section_z_text",
    ]

    for name in names:

        try:

            plotter.remove_actor(
                name
            )

        except Exception:

            pass


# ============================================================
# CREATE SECTION
# ============================================================

def create_sections(
    plotter,
    holder_mesh,
    pcb_mesh,
    lid_mesh,
    z
):

    remove_section_actors(
        plotter
    )

    # --------------------------------------------------------
    # HOLDER
    # --------------------------------------------------------

    holder_section = holder_mesh.slice(
        normal=(
            0,
            0,
            1
        ),
        origin=(
            0,
            0,
            z
        )
    )

    if holder_section.n_points > 0:

        plotter.add_mesh(
            holder_section,
            name="holder_section",
            show_edges=True,
            line_width=3
        )

    # --------------------------------------------------------
    # PCB / STEP
    # --------------------------------------------------------

    pcb_section = pcb_mesh.slice(
        normal=(
            0,
            0,
            1
        ),
        origin=(
            0,
            0,
            z
        )
    )

    if pcb_section.n_points > 0:

        plotter.add_mesh(
            pcb_section,
            name="pcb_section",
            show_edges=True,
            line_width=3
        )

    # --------------------------------------------------------
    # LID
    # --------------------------------------------------------

    lid_section = lid_mesh.slice(
        normal=(
            0,
            0,
            1
        ),
        origin=(
            0,
            0,
            z
        )
    )

    if lid_section.n_points > 0:

        plotter.add_mesh(
            lid_section,
            name="lid_section",
            show_edges=True,
            line_width=3
        )

    # --------------------------------------------------------
    # SECTION LABEL
    # --------------------------------------------------------

    plotter.add_text(
        f"SECTION Z = {z:.2f} mm",
        name="section_z_text",
        position="upper_right",
        font_size=12
    )


# ============================================================
# SECTION CALLBACK
# ============================================================

def create_section_callback(
    plotter,
    holder_mesh,
    pcb_mesh,
    lid_mesh
):

    def callback(z):

        create_sections(
            plotter,
            holder_mesh,
            pcb_mesh,
            lid_mesh,
            float(z)
        )

        plotter.render()

    return callback


# ============================================================
# ADD SECTION SLIDER
# ============================================================

def add_section_slider(
    plotter,
    holder_mesh,
    pcb_mesh,
    lid_mesh
):

    holder_min_z = (
        holder_mesh.bounds[4]
    )

    holder_max_z = (
        holder_mesh.bounds[5]
    )

    callback = create_section_callback(
        plotter,
        holder_mesh,
        pcb_mesh,
        lid_mesh
    )

    initial_z = (
        holder_min_z
        + holder_max_z
    ) / 2.0

    plotter.add_slider_widget(
        callback,
        rng=(
            holder_min_z,
            holder_max_z
        ),
        value=initial_z,
        title="Section Z (mm)",
        pointa=(
            0.03,
            0.08
        ),
        pointb=(
            0.35,
            0.08
        ),
        style="modern"
    )


# ============================================================
# KEYBOARD CALLBACKS
# ============================================================

def add_keyboard_controls(
    plotter,
    assembled_lid,
    exploded_lid,
    lid_actor_name="lid"
):

    state = {

        "exploded": False
    }

    def toggle_exploded():

        state["exploded"] = (
            not state["exploded"]
        )

        if state["exploded"]:

            new_mesh = exploded_lid

        else:

            new_mesh = assembled_lid

        plotter.remove_actor(
            lid_actor_name
        )

        plotter.add_mesh(
            new_mesh,
            name=lid_actor_name,
            opacity=0.30,
            show_edges=True
        )

        plotter.render()

    def show_assembly():

        state["exploded"] = False

        plotter.remove_actor(
            lid_actor_name
        )

        plotter.add_mesh(
            assembled_lid,
            name=lid_actor_name,
            opacity=0.30,
            show_edges=True
        )

        plotter.render()

    def show_exploded():

        state["exploded"] = True

        plotter.remove_actor(
            lid_actor_name
        )

        plotter.add_mesh(
            exploded_lid,
            name=lid_actor_name,
            opacity=0.30,
            show_edges=True
        )

        plotter.render()

    plotter.add_key_event(
        "e",
        toggle_exploded
    )

    plotter.add_key_event(
        "a",
        show_assembly
    )

    plotter.add_key_event(
        "x",
        show_exploded
    )


# ============================================================
# MAIN VISUALIZATION
# ============================================================

def visualize(
    holder,
    lid,
    geometry,
    pcb_mesh,
    mode="assembly",
    config=None
):
    """
    Main visualization entry point.

    Parameters
    ----------
    holder:
        CadQuery holder solid.

    lid:
        CadQuery lid solid in its local coordinate system.

    geometry:
        Shared geometry dictionary.

    pcb_mesh:
        Original STEP mesh.

    mode:
        "assembly"
        "exploded"
        "holder"
        "lid"

    config:
        Optional visualization configuration.
    """

    # ========================================================
    # CONFIG
    # ========================================================

    if config is None:

        config = {}

    cfg = {
        **DEFAULT_CONFIG,
        **config
    }

    # ========================================================
    # Z INFORMATION
    # ========================================================

    z_info = get_z_information(
        geometry
    )

    # ========================================================
    # HOLDER
    # ========================================================

    holder_mesh = cadquery_to_pyvista(
        holder,
        tolerance=cfg["tolerance"]
    )

    # ========================================================
    # LID
    # ========================================================

    lid_mesh = cadquery_to_pyvista(
        lid,
        tolerance=cfg["tolerance"]
    )

    # ========================================================
    # PCB / STEP
    # ========================================================

    pcb_display = pcb_mesh.copy()

    if cfg["align_pcb"]:

        pcb_display = align_pcb_to_holder(
            pcb_display,
            geometry
        )

    # ========================================================
    # ASSEMBLED LID
    # ========================================================

    assembled_lid = create_assembled_lid(
        lid_mesh,
        geometry
    )

    # ========================================================
    # EXPLODED LID
    # ========================================================

    exploded_lid = create_exploded_lid(
        assembled_lid,
        cfg["exploded_distance"]
    )

    # ========================================================
    # SELECT INITIAL LID
    # ========================================================

    if mode == "exploded":

        lid_display = exploded_lid

    else:

        lid_display = assembled_lid

    # ========================================================
    # PLOTTER
    # ========================================================

    plotter = pv.Plotter(
        window_size=(
            1600,
            1000
        )
    )

    # ========================================================
    # HOLDER
    # ========================================================

    if (
        cfg["show_holder"]
        and mode != "lid"
    ):

        plotter.add_mesh(
            holder_mesh,
            name="holder",
            opacity=cfg["holder_opacity"],
            show_edges=True
        )

    # ========================================================
    # PCB / STEP
    # ========================================================

    if (
        cfg["show_pcb"]
        and mode != "lid"
    ):

        plotter.add_mesh(
            pcb_display,
            name="pcb",
            opacity=cfg["pcb_opacity"],
            show_edges=True
        )

    # ========================================================
    # LID
    # ========================================================

    if (
        cfg["show_lid"]
        and mode != "holder"
    ):

        plotter.add_mesh(
            lid_display,
            name="lid",
            opacity=cfg["lid_opacity"],
            show_edges=True
        )

    # ========================================================
    # REFERENCE PLANES
    # ========================================================

    if cfg["show_reference_planes"]:

        add_reference_planes(
            plotter,
            geometry,
            z_info
        )

    # ========================================================
    # INFORMATION
    # ========================================================

    add_information_panels(
        plotter,
        geometry,
        z_info,
        show_geometry=(
            cfg["show_geometry_information"]
        ),
        show_fit=(
            cfg["show_fit_information"]
        )
    )

    # ========================================================
    # TITLE
    # ========================================================

    title = (
        "PCB ENCLOSURE  |  "
        f"{mode.upper()}"
    )

    plotter.add_text(
        title,
        name="title",
        position="upper_left",
        font_size=15
    )

    # ========================================================
    # SECTION
    # ========================================================

    if cfg["enable_section"]:

        add_section_slider(
            plotter,
            holder_mesh,
            pcb_display,
            lid_display
        )

    # ========================================================
    # KEYBOARD CONTROLS
    # ========================================================

    add_keyboard_controls(
        plotter,
        assembled_lid,
        exploded_lid
    )

    # ========================================================
    # AXES
    # ========================================================

    plotter.show_axes()

    # ========================================================
    # GRID
    # ========================================================

    plotter.show_grid(
        location="outer",
        ticks="outside"
    )

    # ========================================================
    # CAMERA
    # ========================================================

    if cfg["view"] == "top":

        plotter.view_xy()

    elif cfg["view"] == "front":

        plotter.view_xz()

    elif cfg["view"] == "right":

        plotter.view_yz()

    else:

        plotter.view_isometric()

    # ========================================================
    # CAMERA RESET
    # ========================================================

    plotter.reset_camera()

    # ========================================================
    # SHOW
    # ========================================================

    plotter.show()