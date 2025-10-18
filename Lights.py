import numpy as np
from MathLibrary import normalize, clamp_01, reflect_vector


class Light(object):
    def __init__(self, color=(1, 1, 1), intensity=1.0, light_type="None"):
        self.color = np.array(color, dtype=float)
        self.intensity = float(intensity)
        self.light_type = light_type

    def get_light_color(self, intercept=None):
        return (self.color * self.intensity).tolist()

    def get_specular_color(self, intercept, view_pos, shininess=32, ks=0.5):
        return [0.0, 0.0, 0.0]


class AmbientLight(Light):
    def __init__(self, color=(1, 1, 1), intensity=0.12):
        super().__init__(color, intensity, "Ambient")

    def get_light_color(self, intercept=None):
        return super().get_light_color()


class DirectionalLight(Light):
    def __init__(self, color=(1, 1, 1), intensity=1.0, direction=(0, -1, 0)):
        super().__init__(color, intensity, "Directional")
        self.direction = normalize(direction)

    def get_light_color(self, intercept=None):
        base = super().get_light_color()
        
        if intercept is None:
            return base
            
        light_dir = -self.direction
        normal = normalize(intercept.normal)
        
        ndotl = clamp_01(np.dot(normal, light_dir))
        
        return (np.array(base) * ndotl).tolist()

    def get_specular_color(self, intercept, view_pos, shininess=64, ks=0.35):
        point = np.array(intercept.point, dtype=float)
        view_dir = normalize(np.array(view_pos, dtype=float) - point)
        light_dir = -self.direction
        reflect_dir = reflect_vector(intercept.normal, light_dir)
        
        spec = clamp_01(np.dot(view_dir, reflect_dir)) ** shininess
        
        return (self.color * self.intensity * ks * spec).tolist()


class PointLight(Light):
    def __init__(self, color=(1, 1, 1), intensity=1.0, position=(0, 0, 0), range_dist=10.0, attenuation=(1.0, 0.09, 0.032)):
        super().__init__(color, intensity, "Point")
        self.position = np.array(position, dtype=float)
        self.range_dist = float(range_dist)
        self.attenuation = tuple(attenuation)

    def get_light_color(self, intercept=None):
        base = super().get_light_color()
        
        if intercept is None:
            return base
            
        point = np.array(intercept.point, dtype=float)
        distance = np.linalg.norm(self.position - point)
        const, lin, quad = self.attenuation
        
        att_factor = 1.0 / max(1e-6, const + lin * distance + quad * (distance * distance))
        
        if distance > self.range_dist:
            att_factor = 0.0
            
        return (np.array(base) * att_factor).tolist()

    def direction_from_point(self, point):
        p_vec = np.array(point, dtype=float)
        v_vec = self.position - p_vec
        norm = np.linalg.norm(v_vec)
        
        if norm == 0:
            return np.array((0.0, 1.0, 0.0))
            
        return v_vec / norm

    def distance_to(self, point):
        return float(np.linalg.norm(self.position - np.array(point, dtype=float)))