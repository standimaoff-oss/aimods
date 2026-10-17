#!/usr/bin/env python3
"""Small deterministic GLB 2.0 writer used by the first WWI asset sources.

The generated meshes are real triangle geometry with UVs, normals, PBR materials, and embedded PNG textures.
This module deliberately uses only the Python standard library so the asset pipeline is reproducible without Blender.
"""
from __future__ import annotations

import json
import math
import struct
import zlib
from pathlib import Path


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png_rgba(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    if len(pixels) != width * height:
        raise ValueError("RGBA pixel count does not match image size")
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixels[y * width + x])
    body = bytes(rows)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + _png_chunk(b"IDAT", zlib.compress(body, 9))
            + _png_chunk(b"IEND", b""))


def solid_texture(width: int, height: int, base: tuple[int, int, int], seed: int,
                  grain: int = 7) -> bytes:
    """Tiled, seeded subtle surface grain; palette variation comes from per-material PBR factors."""
    import random
    rng = random.Random(seed)
    pix = []
    for y in range(height):
        for x in range(width):
            # Two low-frequency wave terms mimic brushed paint/wood without an external image dependency.
            wave = int(2 * math.sin(x * 0.14 + math.sin(y * 0.08)) + 2 * math.sin(y * 0.19))
            n = rng.randrange(-grain, grain + 1) + wave
            pix.append(tuple(max(0, min(255, c + n)) for c in base) + (255,))
    return png_rgba(width, height, pix)


def axis_quaternion(axis: tuple[float, float, float], angle: float) -> list[float]:
    n = math.sqrt(sum(v * v for v in axis))
    if n < 1e-12:
        return [0.0, 0.0, 0.0, 1.0]
    s = math.sin(angle * 0.5) / n
    return [axis[0] * s, axis[1] * s, axis[2] * s, math.cos(angle * 0.5)]


class Mesh:
    """Material-indexed triangle accumulator; triangles use flat per-face normals."""

    def __init__(self) -> None:
        self.groups: dict[int, dict[str, list]] = {}

    def triangle(self, material: int, a, b, c, uvs=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))) -> None:
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        n = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        length = math.sqrt(sum(v * v for v in n)) or 1.0
        n = tuple(v / length for v in n)
        g = self.groups.setdefault(material, {"p": [], "n": [], "uv": [], "i": []})
        for p, uv in zip((a, b, c), uvs):
            g["p"].extend(p)
            g["n"].extend(n)
            g["uv"].extend(uv)
            g["i"].append(len(g["i"]))

    def quad(self, material: int, points, uvs=((0, 0), (1, 0), (1, 1), (0, 1))) -> None:
        a, b, c, d = points
        self.triangle(material, a, b, c, (uvs[0], uvs[1], uvs[2]))
        self.triangle(material, a, c, d, (uvs[0], uvs[2], uvs[3]))

    def box(self, material: int, lo, hi) -> None:
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        faces = [
            ((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)),  # +X
            ((x0,y0,z1),(x0,y1,z1),(x0,y1,z0),(x0,y0,z0)),  # -X
            ((x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)),  # +Y
            ((x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)),  # -Y
            ((x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(x0,y0,z1)),  # +Z
            ((x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)),  # -Z
        ]
        for face in faces:
            self.quad(material, face)

    def oriented_box(self, material: int, center, ex, ey, ez) -> None:
        """Cuboid from three half-axis vectors; useful for tread plates along a sloped track loop."""
        def p(sx, sy, sz):
            return tuple(center[k] + sx * ex[k] + sy * ey[k] + sz * ez[k] for k in range(3))
        self.quad(material, [p(1,-1,-1),p(1,1,-1),p(1,1,1),p(1,-1,1)])
        self.quad(material, [p(-1,-1,1),p(-1,1,1),p(-1,1,-1),p(-1,-1,-1)])
        self.quad(material, [p(-1,1,-1),p(-1,1,1),p(1,1,1),p(1,1,-1)])
        self.quad(material, [p(-1,-1,1),p(-1,-1,-1),p(1,-1,-1),p(1,-1,1)])
        self.quad(material, [p(-1,-1,1),p(1,-1,1),p(1,1,1),p(-1,1,1)])
        self.quad(material, [p(1,-1,-1),p(-1,-1,-1),p(-1,1,-1),p(1,1,-1)])

    def cylinder(self, material: int, start, end, radius: float, sides: int = 12, cap_material: int | None = None) -> None:
        d = tuple(end[i] - start[i] for i in range(3))
        length = math.sqrt(sum(v * v for v in d))
        if length <= 1e-8:
            return
        axis = tuple(v / length for v in d)
        ref = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = (axis[1]*ref[2]-axis[2]*ref[1], axis[2]*ref[0]-axis[0]*ref[2], axis[0]*ref[1]-axis[1]*ref[0])
        un = math.sqrt(sum(v*v for v in u))
        u = tuple(v/un for v in u)
        v = (axis[1]*u[2]-axis[2]*u[1], axis[2]*u[0]-axis[0]*u[2], axis[0]*u[1]-axis[1]*u[0])
        ring0, ring1 = [], []
        for i in range(sides):
            a = math.tau * i / sides
            radial = tuple(radius * (u[k] * math.cos(a) + v[k] * math.sin(a)) for k in range(3))
            ring0.append(tuple(start[k] + radial[k] for k in range(3)))
            ring1.append(tuple(end[k] + radial[k] for k in range(3)))
        for i in range(sides):
            j = (i + 1) % sides
            self.quad(material, [ring0[i], ring0[j], ring1[j], ring1[i]])
            if cap_material is not None:
                self.triangle(cap_material, start, ring0[j], ring0[i])
                self.triangle(cap_material, end, ring1[i], ring1[j])


class GlbBuilder:
    def __init__(self, title: str) -> None:
        self.title = title
        self.binary = bytearray()
        self.nodes: list[dict] = []
        self.meshes: list[dict] = []
        self.materials: list[dict] = []
        self.accessors: list[dict] = []
        self.views: list[dict] = []
        self.animations: list[dict] = []
        self.images: list[dict] = []
        self.textures: list[dict] = []
        self.samplers: list[dict] = []

    def add_material(self, name: str, color=(1.0,1.0,1.0,1.0), metallic=0.0, roughness=0.8) -> int:
        i = len(self.materials)
        self.materials.append({"name": name, "pbrMetallicRoughness": {
            "baseColorFactor": list(color), "metallicFactor": metallic, "roughnessFactor": roughness,
            "baseColorTexture": {"index": 0}}, "doubleSided": False})
        return i

    def add_texture(self, png: bytes, name: str) -> None:
        self._align(4)
        offset = len(self.binary)
        self.binary.extend(png)
        vi = len(self.views)
        self.views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(png)})
        self.images.append({"name": name, "mimeType": "image/png", "bufferView": vi})
        self.textures.append({"sampler": 0, "source": 0})
        self.samplers.append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})

    def add_mesh(self, name: str, mesh: Mesh) -> int:
        primitives = []
        for material, group in sorted(mesh.groups.items()):
            if not group["i"]:
                continue
            pos = self._accessor(group["p"], "VEC3", 5126, 34962, bounds=True)
            nor = self._accessor(group["n"], "VEC3", 5126, 34962)
            uv = self._accessor(group["uv"], "VEC2", 5126, 34962)
            idx = self._accessor(group["i"], "SCALAR", 5123, 34963)
            primitives.append({"attributes": {"POSITION": pos, "NORMAL": nor, "TEXCOORD_0": uv},
                               "indices": idx, "material": material, "mode": 4})
        if not primitives:
            raise ValueError(f"mesh {name} is empty")
        result = len(self.meshes)
        self.meshes.append({"name": name, "primitives": primitives})
        return result

    def add_node(self, name: str, mesh: int | None = None, translation=(0,0,0), rotation=(0,0,0,1),
                 scale=(1,1,1), children=()) -> int:
        node = {"name": name, "translation": list(translation), "rotation": list(rotation), "scale": list(scale)}
        if mesh is not None:
            node["mesh"] = mesh
        if children:
            node["children"] = list(children)
        result = len(self.nodes)
        self.nodes.append(node)
        return result

    def set_children(self, node: int, children) -> None:
        self.nodes[node]["children"] = list(children)

    def add_animation(self, name: str, channels: list[tuple[int, str, list[float], list[float]]]) -> None:
        """Channels are (node, path, key_times, flattened outputs); interpolation is LINEAR."""
        samplers, out_channels = [], []
        for node, path, times, values in channels:
            width = 4 if path == "rotation" else 3
            if len(values) != len(times) * width:
                raise ValueError(f"animation {name}: {path} value count mismatch")
            ti = self._accessor(times, "SCALAR", 5126, 0, bounds=True)
            vi = self._accessor(values, "VEC4" if width == 4 else "VEC3", 5126, 0)
            si = len(samplers)
            samplers.append({"input": ti, "output": vi, "interpolation": "LINEAR"})
            out_channels.append({"sampler": si, "target": {"node": node, "path": path}})
        self.animations.append({"name": name, "samplers": samplers, "channels": out_channels})

    def _align(self, n: int) -> None:
        while len(self.binary) % n:
            self.binary.append(0)

    def _accessor(self, values, kind: str, component: int, target: int, bounds=False) -> int:
        self._align(4)
        fmt = {5123: "H", 5125: "I", 5126: "f"}[component]
        size = struct.calcsize("<" + fmt)
        packed = struct.pack("<" + fmt * len(values), *values)
        offset = len(self.binary)
        self.binary.extend(packed)
        vi = len(self.views)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(packed)}
        if target:
            view["target"] = target
        self.views.append(view)
        width = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[kind]
        accessor = {"bufferView":vi,"componentType":component,"count":len(values)//width,"type":kind}
        if bounds and values:
            rows=[values[i:i+width] for i in range(0,len(values),width)]
            accessor["min"]=[min(row[c] for row in rows) for c in range(width)]
            accessor["max"]=[max(row[c] for row in rows) for c in range(width)]
        ai=len(self.accessors)
        self.accessors.append(accessor)
        return ai

    def save(self, path: Path, scene_roots: list[int]) -> None:
        if not self.materials or not self.images:
            raise ValueError("GLB needs textured materials")
        self._align(4)
        doc = {"asset":{"version":"2.0","generator":"aiarsenal WWI procedural source: " + self.title},
               "scene":0,"scenes":[{"nodes":scene_roots}],"nodes":self.nodes,"meshes":self.meshes,
               "materials":self.materials,"textures":self.textures,"samplers":self.samplers,"images":self.images,
               "buffers":[{"byteLength":len(self.binary)}],"bufferViews":self.views,"accessors":self.accessors,
               "animations":self.animations}
        jb=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode("utf-8")
        while len(jb)%4: jb+=b" "
        total=12+8+len(jb)+8+len(self.binary)
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("wb") as f:
            f.write(struct.pack("<III",0x46546C67,2,total))
            f.write(struct.pack("<I",len(jb))+b"JSON"+jb)
            f.write(struct.pack("<I",len(self.binary))+b"BIN\0"+self.binary)
