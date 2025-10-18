import math
import numpy as np
from Interception import Intercept


def _norm(v):
    v = np.array(v, dtype=float)
    norm_val = np.linalg.norm(v)
    return v if norm_val == 0 else v / norm_val


class Sphere:
    def __init__(self, position, radius, material):
        self.center = np.array(position, dtype=float)
        self.radius = float(radius)
        self.material = material

    def ray_intersect(self, orig, direction):
        l_vec = self.center - orig
        tca = np.dot(l_vec, direction)
        
        d2 = np.dot(l_vec, l_vec) - tca * tca
        r2 = self.radius * self.radius
        
        if d2 > r2:
            return None
            
        thc = np.sqrt(r2 - d2)
        t0 = tca - thc
        t1 = tca + thc
        t = t0 if t0 > 1e-4 else t1
        
        if t <= 1e-4:
            return None
            
        point = orig + direction * t
        normal = _norm(point - self.center)
        
        return Intercept(point, normal, t, direction, self, uv=None)


class Plane:
    def __init__(self, position, normal, material, tex_scale=1.0):
        self.p0 = np.array(position, dtype=float)
        self.normal = _norm(normal)
        self.material = material
        self.tex_scale = float(tex_scale)

    def ray_intersect(self, orig, direction):
        denom = np.dot(direction, self.normal)
        
        if abs(denom) < 1e-6:
            return None
            
        t = np.dot(self.p0 - orig, self.normal) / denom
        
        if t <= 1e-4:
            return None
            
        point = orig + direction * t
        
        if abs(self.normal[1]) > 0.9:
            u = point[0] * self.tex_scale
            v = point[2] * self.tex_scale
            u = u - np.floor(u)
            v = v - np.floor(v)
            uv = (u, v)
        else:
            uv = None
            
        return Intercept(point, self.normal, t, direction, self, uv=uv)


class Disk(Plane):
    def __init__(self, position, normal, radius, material):
        super().__init__(position, normal, material)
        self.center = np.array(position, dtype=float)
        self.radius = float(radius)

    def ray_intersect(self, orig, direction):
        hit = super().ray_intersect(orig, direction)
        
        if hit is None:
            return None
            
        if np.linalg.norm(hit.point - self.center) <= self.radius + 1e-6:
            return hit
            
        return None


class Triangle:
    def __init__(self, a, b, c, material, uv_a=None, uv_b=None, uv_c=None):
        self.a = np.array(a, dtype=float)
        self.b = np.array(b, dtype=float)
        self.c = np.array(c, dtype=float)
        self.material = material
        self.normal = _norm(np.cross(self.b - self.a, self.c - self.a))
        
        self.uv_a = np.array(uv_a, dtype=float) if uv_a is not None else None
        self.uv_b = np.array(uv_b, dtype=float) if uv_b is not None else None
        self.uv_c = np.array(uv_c, dtype=float) if uv_c is not None else None

    def ray_intersect(self, orig, direction):
        denom = np.dot(direction, self.normal)
        
        if abs(denom) < 1e-6:
            return None
            
        t = np.dot(self.a - orig, self.normal) / denom
        
        if t <= 1e-4:
            return None
            
        point = orig + t * direction
        
        def edge(p0, p1):
            return np.cross(p1 - p0, point - p0)
            
        if (np.dot(self.normal, edge(self.a, self.b)) < -1e-6 or
            np.dot(self.normal, edge(self.b, self.c)) < -1e-6 or
            np.dot(self.normal, edge(self.c, self.a)) < -1e-6):
            return None
            
        uv = None
        
        if self.uv_a is not None and self.uv_b is not None and self.uv_c is not None:
            v0 = self.b - self.a
            v1 = self.c - self.a
            v2 = point - self.a
            
            d00 = np.dot(v0, v0)
            d01 = np.dot(v0, v1)
            d11 = np.dot(v1, v1)
            d20 = np.dot(v2, v0)
            d21 = np.dot(v2, v1)
            
            denom_bary = d00 * d11 - d01 * d01
            
            if abs(denom_bary) > 1e-12:
                inv_denom = 1.0 / denom_bary
                v = (d11 * d20 - d01 * d21) * inv_denom
                w = (d00 * d21 - d01 * d20) * inv_denom
                u = 1.0 - v - w
            else:
                u = v = w = 1.0 / 3.0
                
            uv = u * self.uv_a + v * self.uv_b + w * self.uv_c
            
        return Intercept(point, self.normal, t, direction, self, uv=uv)


class AABB:
    def __init__(self, position, sizes, material):
        self.center = np.array(position, dtype=float)
        self.half = np.array(sizes, dtype=float) * 0.5
        self.material = material

    def ray_intersect(self, orig, direction):
        t_min = -np.inf
        t_max = np.inf
        normal_min = None
        normal_max = None
        
        for axis in range(3):
            min_plane = self.center[axis] - self.half[axis]
            max_plane = self.center[axis] + self.half[axis]
            
            if abs(direction[axis]) < 1e-8:
                if orig[axis] < min_plane or orig[axis] > max_plane:
                    return None
                continue
                
            inv_d = 1.0 / direction[axis]
            t0 = (min_plane - orig[axis]) * inv_d
            t1 = (max_plane - orig[axis]) * inv_d
            
            if inv_d >= 0:
                n0 = np.zeros(3)
                n0[axis] = -1
                n1 = np.zeros(3)
                n1[axis] = 1
            else:
                n0 = np.zeros(3)
                n0[axis] = 1
                n1 = np.zeros(3)
                n1[axis] = -1
                
            if t0 > t1:
                t0, t1 = t1, t0
                n0, n1 = n1, n0
                
            if t0 > t_min:
                t_min = t0
                normal_min = n0
                
            if t1 < t_max:
                t_max = t1
                normal_max = n1
                
            if t_min > t_max:
                return None
                
        t = t_min if t_min > 1e-4 else t_max
        
        if t <= 1e-4:
            return None
            
        point = orig + direction * t
        normal = normal_min if t == t_min else normal_max
        
        min_corner = self.center - self.half
        max_corner = self.center + self.half
        
        nx, ny, nz = normal
        
        if abs(nx) > 0.5:
            u = (point[2] - min_corner[2]) / (max_corner[2] - min_corner[2])
            v = (point[1] - min_corner[1]) / (max_corner[1] - min_corner[1])
        elif abs(ny) > 0.5:
            u = (point[0] - min_corner[0]) / (max_corner[0] - min_corner[0])
            v = (point[2] - min_corner[2]) / (max_corner[2] - min_corner[2])
        else:
            u = (point[0] - min_corner[0]) / (max_corner[0] - min_corner[0])
            v = (point[1] - min_corner[1]) / (max_corner[1] - min_corner[1])
            
        u = max(0.0, min(1.0, float(u)))
        v = max(0.0, min(1.0, float(v)))
        
        return Intercept(point, normal, t, direction, self, uv=(u, v))


class Cylinder:
    def __init__(self, center, axis, radius, height, material):
        self.center = np.array(center, dtype=float)
        self.axis = _norm(axis)
        self.radius = float(radius)
        self.height = float(height)
        self.material = material
        
        half_height = self.height * 0.5
        self.bottom = self.center - self.axis * half_height
        self.top = self.center + self.axis * half_height
        
        if abs(self.axis[0]) < 0.9:
            tmp = np.array([1, 0, 0], dtype=float)
        else:
            tmp = np.array([0, 0, 1], dtype=float)
            
        self.u_vec = _norm(np.cross(self.axis, tmp))
        self.v_vec = _norm(np.cross(self.axis, self.u_vec))

    def ray_intersect(self, orig, direction):
        oc = orig - self.center
        
        dir_parallel = np.dot(direction, self.axis) * self.axis
        dir_perp = direction - dir_parallel
        
        oc_parallel = np.dot(oc, self.axis) * self.axis
        oc_perp = oc - oc_parallel
        
        a = np.dot(dir_perp, dir_perp)
        b = 2.0 * np.dot(oc_perp, dir_perp)
        c = np.dot(oc_perp, oc_perp) - self.radius * self.radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
            
        if abs(a) < 1e-8:
            if c > 0:
                return None
            return self._intersect_caps(orig, direction)
            
        sqrt_disc = np.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        
        candidates = []
        
        for t in [t1, t2]:
            if t <= 1e-4:
                continue
                
            point = orig + direction * t
            height_param = np.dot(point - self.center, self.axis)
            
            if abs(height_param) <= self.height * 0.5:
                center_to_point = point - self.center
                normal_component = center_to_point - np.dot(center_to_point, self.axis) * self.axis
                normal = _norm(normal_component)
                candidates.append((t, point, normal))
                
        cap_result = self._intersect_caps(orig, direction)
        
        if cap_result is not None:
            candidates.append((cap_result.distance, cap_result.point, cap_result.normal))
            
        if not candidates:
            return None
            
        candidates.sort(key=lambda x: x[0])
        t, point, normal = candidates[0]
        
        rel = point - self.center
        x_val = float(np.dot(rel, self.u_vec))
        y_val = float(np.dot(rel, self.v_vec))
        z_val = float(np.dot(rel, self.axis))
        
        theta = math.atan2(y_val, x_val)
        u = (theta / (2.0 * math.pi)) % 1.0
        v = (z_val / self.height) + 0.5
        
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        
        return Intercept(point, normal, t, direction, self, uv=(u, v))

    def _intersect_caps(self, orig, direction):
        candidates = []
        
        for cap_center, cap_normal in [(self.bottom, -self.axis), (self.top, self.axis)]:
            denom = np.dot(direction, cap_normal)
            
            if abs(denom) < 1e-6:
                continue
                
            t = np.dot(cap_center - orig, cap_normal) / denom
            
            if t <= 1e-4:
                continue
                
            point = orig + direction * t
            dist_from_center = np.linalg.norm(point - cap_center)
            
            if dist_from_center <= self.radius:
                candidates.append((t, point, cap_normal))
                
        if not candidates:
            return None
            
        candidates.sort(key=lambda x: x[0])
        t, point, normal = candidates[0]
        
        return Intercept(point, normal, t, direction, self, uv=None)