import numpy as np
from PIL import Image
from MathLibrary import reflect_vector
from Refraction import refract_vector, total_internal_reflection, fresnel


OPAQUE = "OPAQUE"
REFLECTIVE = "REFLECTIVE"
TRANSPARENT = "TRANSPARENT"


class Material(object):
    def __init__(self, diffuse=(1, 1, 1), ka=0.1, kd=0.9, ks=0.35, shininess=64, mat_type=OPAQUE, ior=1.0, reflectivity=0.0, texture_path=None, tex_brightness=1.0, emissive=(0.0, 0.0, 0.0)):
        self.diffuse = np.array(diffuse, dtype=float)
        self.ka = float(ka)
        self.kd = float(kd)
        self.ks = float(ks)
        self.shininess = float(shininess)
        self.mat_type = mat_type
        self.ior = float(ior)
        self.reflectivity = float(reflectivity)
        self.texture = None
        self.tex_w = 0
        self.tex_h = 0
        self.tex_brightness = float(tex_brightness)
        self.emissive = np.array(emissive, dtype=float)
        
        if texture_path is not None:
            try:
                img = Image.open(texture_path).convert("RGB")
                tex = np.asarray(img).astype(np.float32) / 255.0
                self.texture = tex
                self.tex_h, self.tex_w, _ = tex.shape
            except Exception:
                self.texture = None

    def sample_texture(self, uv):
        if self.texture is None or uv is None:
            return self.diffuse
            
        u, v = uv
        u = float(u) % 1.0
        v = float(v) % 1.0
        
        x = int(u * (self.tex_w - 1))
        y = int((1.0 - v) * (self.tex_h - 1))
        
        col = self.texture[y, x]
        col = np.clip(col * self.tex_brightness, 0.0, 1.0)
        
        return col

    def get_surface_color(self, intercept, renderer, recursion=0):
        normal = intercept.normal / (np.linalg.norm(intercept.normal) + 1e-8)
        view_dir = -intercept.ray_direction
        view_dir /= np.linalg.norm(view_dir) + 1e-8
        
        ambient = np.zeros(3, dtype=float)
        for light in renderer.lights:
            if getattr(light, "light_type", "") == "Ambient":
                ambient += np.array(light.get_light_color(), dtype=float)
                
        diffuse_light = np.zeros(3, dtype=float)
        specular_light = np.zeros(3, dtype=float)
        
        for light in renderer.lights:
            light_type = getattr(light, "light_type", "")
            
            if light_type == "Directional":
                light_dir = -np.array(light.direction, dtype=float)
                light_dir /= np.linalg.norm(light_dir) + 1e-8
                attenuation = 1.0
                
            elif light_type == "Point":
                light_dir = light.direction_from_point(intercept.point)
                distance = light.distance_to(intercept.point)
                const, lin, quad = getattr(light, "attenuation", (1.0, 0.0, 0.0))
                attenuation = 1.0 / max(1e-6, const + lin * distance + quad * distance * distance)
                
            else:
                continue
                
            shadow_origin = intercept.point + normal * 1e-3
            # CORRECCIÓN: Usamos scene_intersect en lugar de cast_ray para evitar recursión infinita en sombras
            shadow_hit = renderer.scene_intersect(shadow_origin, light_dir, intercept.obj)
            
            if shadow_hit is not None:
                if light_type == "Point":
                    if shadow_hit.distance < light.distance_to(shadow_origin) - 1e-3:
                        continue
                else:
                    continue
                    
            ndotl = max(0.0, float(np.dot(normal, light_dir)))
            diffuse_light += np.array(light.color, dtype=float) * light.intensity * ndotl * attenuation
            
            reflect_dir = reflect_vector(normal, -light_dir)
            rdotv = max(0.0, float(np.dot(reflect_dir, view_dir)))
            specular_light += np.array(light.color, dtype=float) * (rdotv ** self.shininess) * light.intensity * attenuation
            
        base_color = self.sample_texture(getattr(intercept, "uv", None))
        final_base = base_color * (self.ka * ambient + self.kd * diffuse_light) + self.ks * specular_light + self.emissive
        final_base = np.clip(final_base, 0.0, 1.0)
        
        if self.mat_type == REFLECTIVE:
            if recursion >= renderer.max_depth:
                return tuple(final_base)
                
            reflect_dir = reflect_vector(normal, view_dir)
            reflect_origin = intercept.point + normal * 1e-3
            
            # CORRECCIÓN: Usamos scene_intersect para obtener el objeto golpeado
            reflect_hit = renderer.scene_intersect(reflect_origin, reflect_dir, intercept.obj)
            
            if reflect_hit is not None:
                reflect_col = reflect_hit.obj.material.get_surface_color(reflect_hit, renderer, recursion + 1)
            else:
                reflect_col = renderer.get_env_map_color(reflect_origin, reflect_dir)
                
            color = (1.0 - self.reflectivity) * final_base + self.reflectivity * np.array(reflect_col)
            
            return tuple(np.clip(color, 0.0, 1.0))
            
        if self.mat_type == TRANSPARENT:
            if recursion >= renderer.max_depth:
                return tuple(final_base)
                
            is_outside = float(np.dot(normal, intercept.ray_direction)) < 0.0
            normal_use = normal if is_outside else -normal
            bias = normal_use * 1e-3
            
            kr, kt = fresnel(normal_use, -view_dir, 1.0, self.ior)
            
            reflect_dir = reflect_vector(normal_use, view_dir)
            reflect_origin = intercept.point + bias
            
            # CORRECCIÓN: Usamos scene_intersect
            reflect_hit = renderer.scene_intersect(reflect_origin, reflect_dir, None)
            
            if reflect_hit is not None:
                reflect_col = reflect_hit.obj.material.get_surface_color(reflect_hit, renderer, recursion + 1)
            else:
                reflect_col = renderer.get_env_map_color(reflect_origin, reflect_dir)
                
            if not total_internal_reflection(normal_use, -view_dir, 1.0, self.ior):
                refract_dir = refract_vector(normal_use, -view_dir, 1.0, self.ior)
                
                if refract_dir is not None:
                    refract_origin = intercept.point - bias
                    # CORRECCIÓN: Usamos scene_intersect
                    refract_hit = renderer.scene_intersect(refract_origin, refract_dir, None)
                    
                    if refract_hit is not None:
                        refract_col = refract_hit.obj.material.get_surface_color(refract_hit, renderer, recursion + 1)
                    else:
                        refract_col = renderer.get_env_map_color(refract_origin, refract_dir)
                else:
                    kt = 0.0
                    refract_col = np.zeros(3)
            else:
                kt = 0.0
                refract_col = np.zeros(3)
                
            color = kr * np.array(reflect_col) + kt * np.array(refract_col)
            
            return tuple(np.clip(color, 0.0, 1.0))
            
        return tuple(final_base)