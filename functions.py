import tempfile

import cadquery as cq
import cv2
import numpy as np
import pyvista as pv

from scipy.spatial import ConvexHull


PCB_LAYER_PERCENT = 0.15


def load_mesh(stepfile):
    part = cq.importers.importStep(stepfile)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".stl",
        delete=False
    )

    cq.exporters.export(part, tmp.name)

    return pv.read(tmp.name)


def fit_circle(points):
    x = points[:, 0]
    y = points[:, 1]

    x_m = np.mean(x)
    y_m = np.mean(y)

    u = x - x_m
    v = y - y_m

    Suu = np.sum(u * u)
    Svv = np.sum(v * v)
    Suv = np.sum(u * v)

    Suuu = np.sum(u * u * u)
    Svvv = np.sum(v * v * v)

    Suuv = np.sum(u * u * v)
    Suvv = np.sum(u * v * v)

    A = np.array([
        [Suu, Suv],
        [Suv, Svv]
    ])

    B = np.array([
        (Suuu + Suvv) / 2.0,
        (Svvv + Suuv) / 2.0
    ])

    uc, vc = np.linalg.solve(A, B)

    xc = x_m + uc
    yc = y_m + vc

    r = np.mean(
        np.sqrt(
            (x - xc) ** 2 +
            (y - yc) ** 2
        )
    )

    return xc, yc, r


def refine_hole_local(
    xy,
    hole,
    search_factor=1.5
):
    cx, cy, r = hole

    search = r * search_factor

    pts = xy[
        (xy[:, 0] >= cx - search) &
        (xy[:, 0] <= cx + search) &
        (xy[:, 1] >= cy - search) &
        (xy[:, 1] <= cy + search)
    ]

    if len(pts) < 20:
        return hole

    dist = np.sqrt(
        (pts[:, 0] - cx) ** 2 +
        (pts[:, 1] - cy) ** 2
    )

    ring = pts[
        (dist >= r * 0.6) &
        (dist <= r * 1.4)
    ]

    if len(ring) < 12:
        return hole

    try:
        return fit_circle(ring)

    except Exception:
        return hole


def pcb_points(mesh, layer_percent=PCB_LAYER_PERCENT):
    z = mesh.points[:, 2]

    zmin = z.min()
    zmax = z.max()

    limit = zmin + (
        zmax - zmin
    ) * layer_percent

    return mesh.points[z <= limit]


def contour(points):
    xy = points[:, :2]

    hull = ConvexHull(xy)

    result = xy[hull.vertices]

    return np.vstack([
        result,
        result[0]
    ])


def points_to_image(xy, scale=12):
    minx = np.min(xy[:, 0])
    maxx = np.max(xy[:, 0])

    miny = np.min(xy[:, 1])
    maxy = np.max(xy[:, 1])

    padding = 20

    width = int((maxx - minx) * scale) + padding * 2
    height = int((maxy - miny) * scale) + padding * 2

    image = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    for x, y in xy:

        px = int((x - minx) * scale) + padding
        py = int((y - miny) * scale) + padding

        cv2.circle(
            image,
            (px, py),
            1,
            255,
            -1
        )

    return image, minx, miny, scale, padding


def detect_corner_holes_hough(
    xy,
    contour_pts,
    corner_mm=4
):
    (
        image,
        minx,
        miny,
        scale,
        padding
    ) = points_to_image(xy)

    image = cv2.GaussianBlur(
        image,
        (5, 5),
        0
    )

    mincx = np.min(contour_pts[:, 0])
    maxcx = np.max(contour_pts[:, 0])

    mincy = np.min(contour_pts[:, 1])
    maxcy = np.max(contour_pts[:, 1])

    corners = [
        ("TL", mincx, maxcy),
        ("TR", maxcx, maxcy),
        ("BL", mincx, mincy),
        ("BR", maxcx, mincy)
    ]

    holes = []

    for _, cx, cy in corners:

        px = int((cx - minx) * scale) + padding
        py = int((cy - miny) * scale) + padding

        win = int(corner_mm * scale)

        x0 = max(0, px - win)
        x1 = min(image.shape[1], px + win)

        y0 = max(0, py - win)
        y1 = min(image.shape[0], py + win)

        roi = image[y0:y1, x0:x1]

        circles = cv2.HoughCircles(
            roi,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=10,
            minRadius=4,
            maxRadius=40
        )

        if circles is None:
            continue

        circles = np.round(
            circles[0]
        ).astype(int)

        circles = sorted(
            circles,
            key=lambda c: c[2],
            reverse=True
        )

        xx, yy, rr = circles[0]

        world_x = (
            x0 + xx - padding
        ) / scale + minx

        world_y = (
            y0 + yy - padding
        ) / scale + miny

        holes.append(
            (
                world_x,
                world_y,
                rr / scale
            )
        )

    return holes


def find_mounting_holes(
    pcb_xy,
    contour_pts,
    corner_mm=4
):
    raw_holes = detect_corner_holes_hough(
        pcb_xy,
        contour_pts,
        corner_mm=corner_mm
    )

    return [
        refine_hole_local(pcb_xy, hole)
        for hole in raw_holes
    ]