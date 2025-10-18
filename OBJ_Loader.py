import os
import numpy as np
from Figures import Triangle
from Materials import Material


def _clone_material_with_texture(base_mat, texture_path):
    tex_mat = Material(
        diffuse=tuple(base_mat.diffuse),
        ka=base_mat.ka,
        kd=base_mat.kd,
        ks=base_mat.ks,
        shininess=base_mat.shininess,
        mat_type=base_mat.mat_type,
        ior=getattr(base_mat, "ior", 1.0),
        reflectivity=getattr(base_mat, "reflectivity", 0.0),
        texture_path=texture_path,
    )
    
    if hasattr(base_mat, "emissive"):
        tex_mat.emissive = base_mat.emissive
        
    if hasattr(base_mat, "tex_brightness"):
        tex_mat.tex_brightness = base_mat.tex_brightness
        
    return tex_mat


def load_obj_as_triangles(path, base_material, scale=1.0, translate=(0, 0, 0)):
    base_dir = os.path.dirname(path) or "."
    vertices = []
    uvs = []
    faces = []
    current_mtl = None
    mtl_file = None
    
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith("#"):
                    continue
                    
                if line.startswith("mtllib"):
                    parts = line.split()
                    if len(parts) >= 2:
                        mtl_file = parts[1]
                        
                elif line.startswith("usemtl"):
                    parts = line.split()
                    if len(parts) >= 2:
                        current_mtl = parts[1]
                        
                elif line.startswith("v "):
                    _, x, y, z = line.split()[:4]
                    vertices.append((float(x), float(y), float(z)))
                    
                elif line.startswith("vt "):
                    parts = line.split()
                    if len(parts) >= 3:
                        _, u, v = parts[:3]
                        uvs.append((float(u), float(v)))
                        
                elif line.startswith("f "):
                    parts = line.split()[1:]
                    raw_face = []
                    for p in parts:
                        vals = p.split("/")
                        vi = int(vals[0]) - 1
                        ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] != "" else None
                        raw_face.append((vi, ti))
                        
                    if len(raw_face) < 3:
                        continue
                        
                    for i in range(1, len(raw_face) - 1):
                        tri = (raw_face[0], raw_face[i], raw_face[i + 1])
                        faces.append((tri, current_mtl))
                        
    except FileNotFoundError:
        return []
        
    mtl_map = {}
    
    if mtl_file is not None:
        mtl_path = os.path.join(base_dir, mtl_file)
        
        if os.path.exists(mtl_path):
            current = None
            with open(mtl_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("newmtl"):
                        parts = line.split()
                        if len(parts) >= 2:
                            current = parts[1]
                    elif line.startswith("map_Kd") and current is not None:
                        parts = line.split()
                        if len(parts) >= 2:
                            tex_name = parts[1]
                            tex_path = os.path.join(base_dir, tex_name)
                            mtl_map[current] = tex_path
                            
    scale_factor = float(scale)
    translate_vec = np.array(translate, dtype=float)
    verts = [scale_factor * np.array(v, dtype=float) + translate_vec for v in vertices]
    
    mat_by_mtl = {}
    
    for _, mtl_name in faces:
        if mtl_name is None:
            continue
        if mtl_name in mat_by_mtl:
            continue
            
        tex_path = mtl_map.get(mtl_name)
        
        if tex_path is not None and os.path.exists(tex_path):
            mat_by_mtl[mtl_name] = _clone_material_with_texture(base_material, tex_path)
        else:
            mat_by_mtl[mtl_name] = base_material
            
    triangles = []
    
    for (tri, mtl_name) in faces:
        (vi0, ti0), (vi1, ti1), (vi2, ti2) = tri
        
        a_point = verts[vi0]
        b_point = verts[vi1]
        c_point = verts[vi2]
        
        uv_a = uvs[ti0] if (ti0 is not None and 0 <= ti0 < len(uvs)) else None
        uv_b = uvs[ti1] if (ti1 is not None and 0 <= ti1 < len(uvs)) else None
        uv_c = uvs[ti2] if (ti2 is not None and 0 <= ti2 < len(uvs)) else None
        
        if mtl_name is not None and mtl_name in mat_by_mtl:
            mat = mat_by_mtl[mtl_name]
        else:
            mat = base_material
            
        triangles.append(Triangle(a_point, b_point, c_point, mat, uv_a=uv_a, uv_b=uv_b, uv_c=uv_c))
        
    return triangles