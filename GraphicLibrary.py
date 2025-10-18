import numpy as np
from PIL import Image
import os
import contextlib
try:
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            import pygame
    _HAS_PYGAME = True
except Exception:
    _HAS_PYGAME = False

class Renderer:
    def __init__(self, width, height, fov=60, bg_color=(0, 0, 0), ssaa=1):
        self.width = int(width)
        self.height = int(height)
        self.aspect = self.width / self.height
        self.fov = np.deg2rad(fov)
        self.tan_fov = np.tan(self.fov * 0.5)
        self.framebuffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.ssaa = int(ssaa) if ssaa >= 1 else 1
        self.cam_pos = np.array((0.0, 0.0, 0.0), dtype=float)
        self.bg_color = np.array(bg_color, dtype=float)
        self.objects = []
        self.lights = []
        self.max_depth = 3
        self.env = None
        self.env_yaw = 0.0
        self.env_vflip = False

    @staticmethod
    def _to_u8(color01):
        return (np.clip(color01, 0.0, 1.0) * 255).astype(np.uint8)

    def add_object(self, obj):
        self.objects.append(obj)

    def add_light(self, light):
        self.lights.append(light)

    def _rot_y(self, v, yaw_rad):
        cy, sy = np.cos(yaw_rad), np.sin(yaw_rad)
        x, y, z = v
        return np.array([cy * x + sy * z, y, -sy * x + cy * z], dtype=float)

    def load_env_map(self, path, yaw_deg=0.0, vflip=False):
        try:
            img = Image.open(path).convert("RGB")
            self.env = np.asarray(img).astype(np.float32) / 255.0
            self.env_yaw = float(yaw_deg)
            self.env_vflip = bool(vflip)
        except Exception:
            self.env = None

    def _sample_env_bilinear(self, u, v):
        h, w, _ = self.env.shape
        u = (u % 1.0) * w
        v = np.clip(v, 0.0, 0.999999) * h
        x0 = int(np.floor(u)) % w
        y0 = int(np.floor(v)) % h
        x1 = (x0 + 1) % w
        y1 = min(y0 + 1, h - 1)
        sx = u - np.floor(u)
        sy = v - np.floor(v)
        c00 = self.env[y0, x0]
        c10 = self.env[y0, x1]
        c01 = self.env[y1, x0]
        c11 = self.env[y1, x1]
        c0 = c00 * (1 - sx) + c10 * sx
        c1 = c01 * (1 - sx) + c11 * sx
        return c0 * (1 - sy) + c1 * sy

    def get_env_map_color(self, point, direction):
        if self.env is None:
            return tuple(self.bg_color)
        d = np.array(direction, dtype=float)
        d /= (np.linalg.norm(d) + 1e-8)
        if self.env_yaw != 0.0:
            d = self._rot_y(d, np.deg2rad(self.env_yaw))
        u = 0.5 + np.arctan2(-d[2], d[0]) / (2 * np.pi)
        v = 0.5 - np.arcsin(np.clip(d[1], -1, 1)) / np.pi
        if self.env_vflip:
            v = 1.0 - v
        return tuple(self._sample_env_bilinear(u, v))

    def render(self, row_callback=None):
        if self.ssaa == 1:
            for j in range(self.height):
                y = (1 - 2 * ((j + 0.5) / self.height)) * self.tan_fov
                for i in range(self.width):
                    x = (2 * ((i + 0.5) / self.width) - 1) * self.tan_fov * self.aspect
                    dir_cam = np.array((x, y, -1.0), dtype=float)
                    dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)
                    color = self.cast_ray(self.cam_pos, dir_cam)
                    self.framebuffer[j, i] = self._to_u8(color)
                if row_callback:
                    row_callback(j)
            return
        h_hr = self.height * self.ssaa
        w_hr = self.width * self.ssaa
        hr_buf = np.zeros((h_hr, w_hr, 3), dtype=np.float32)
        for j in range(h_hr):
            y = (1 - 2 * ((j + 0.5) / h_hr)) * self.tan_fov
            for i in range(w_hr):
                x = (2 * ((i + 0.5) / w_hr) - 1) * self.tan_fov * self.aspect
                dir_cam = np.array((x, y, -1.0), dtype=float)
                dir_cam /= (np.linalg.norm(dir_cam) + 1e-8)
                hr_buf[j, i] = np.array(self.cast_ray(self.cam_pos, dir_cam), dtype=np.float32)
            if row_callback and (j % self.ssaa) == 0:
                row_callback(j // self.ssaa)
            if (j % self.ssaa) == (self.ssaa - 1):
                y_low = j // self.ssaa
                y0 = y_low * self.ssaa
                y1 = y0 + self.ssaa
                for x_low in range(self.width):
                    x0 = x_low * self.ssaa
                    x1 = x0 + self.ssaa
                    block = hr_buf[y0:y1, x0:x1]
                    avg = block.mean(axis=(0, 1))
                    self.framebuffer[y_low, x_low] = self._to_u8(avg)

    def cast_ray(self, origin, direction, recursion=0):
        o_vec = np.array(origin, dtype=float)
        d_vec = np.array(direction, dtype=float)
        d_vec /= (np.linalg.norm(d_vec) + 1e-8)
        hit = self.scene_intersect(o_vec, d_vec)
        if hit is None:
            return self.get_env_map_color(o_vec, d_vec) if self.env is not None else self.bg_color
        return hit.obj.material.get_surface_color(hit, self, recursion)

    def scene_intersect(self, origin, direction, ignore_obj=None):
        o_vec = np.array(origin, dtype=float)
        d_vec = np.array(direction, dtype=float)
        d_vec /= (np.linalg.norm(d_vec) + 1e-8)
        nearest_hit = None
        nearest_t = float("inf")
        for obj in self.objects:
            if obj is ignore_obj:
                continue
            hit = obj.ray_intersect(o_vec, d_vec)
            if hit and 1e-4 < hit.distance < nearest_t:
                nearest_hit = hit
                nearest_t = hit.distance
        return nearest_hit

    def save_bmp(self, filename):
        fb = self.framebuffer.copy().astype(np.uint8)
        h, w, _ = fb.shape
        max_vals = fb.max(axis=(0, 1)).astype(int)
        max_overall = int(max_vals.max())
        if 0 < max_overall < 48:
            scale = min(230.0 / max_overall, 255.0)
            fb = np.clip((fb.astype(np.float32) * scale), 0, 255).astype(np.uint8)
        row_stride = w * 3
        row_padded = (row_stride + 3) & ~3
        padding = row_padded - row_stride
        filesize = 14 + 40 + row_padded * h
        with open(filename, "wb") as f:
            f.write(b"BM")
            f.write(filesize.to_bytes(4, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((0).to_bytes(2, "little"))
            f.write((14 + 40).to_bytes(4, "little"))
            f.write((40).to_bytes(4, "little"))
            f.write(w.to_bytes(4, "little", signed=True))
            f.write(h.to_bytes(4, "little", signed=True))
            f.write((1).to_bytes(2, "little"))
            f.write((24).to_bytes(2, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((row_padded * h).to_bytes(4, "little"))
            f.write((2835).to_bytes(4, "little"))
            f.write((2835).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            pad = b"\x00" * padding
            for y in range(h - 1, -1, -1):
                row = fb[y]
                bgr = row[:, [2, 1, 0]]
                f.write(bgr.tobytes())
                if padding:
                    f.write(pad)