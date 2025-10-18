import sys
import time
import numpy as np
from GraphicLibrary import Renderer
from Figures import Plane, Sphere, Cylinder, AABB
from Lights import AmbientLight, DirectionalLight, PointLight
from Materials import Material, OPAQUE, REFLECTIVE
from OBJ_Loader import load_obj_as_triangles


CONSOLE_WIDTH = 70


def print_header():
    line = "#" * CONSOLE_WIDTH
    title = "RAY TRACING"
    print(line)
    print(title.center(CONSOLE_WIDTH))
    print(line)


def choose_resolution():
    args = sys.argv
    
    if "--low" in args:
        width, height = 256, 144
        print_header()
        print(f"RESOLUCIÓN: {width} × {height}\n")
        return width, height, 1
        
    if "--high" in args:
        width, height = 1280, 720
        print_header()
        print(f"RESOLUCIÓN: {width} × {height}\n")
        return width, height, 1
        
    print_header()
    print()
    
    while True:
        try:
            width = int(input("Ingresa el Ancho de Renderizado en Píxeles: "))
            if width > 0:
                break
        except ValueError:
            pass
        print("[ERROR] - Ingresa un Número Entero Positivo.")
        
    while True:
        try:
            height = int(input("Ingresa el Alto de Renderizado en Píxeles: "))
            if height > 0:
                break
        except ValueError:
            pass
        print("[ERROR] - Ingresa un Número Entero Positivo.")
        
    print()
    print(f"RESOLUCIÓN: {width} × {height}\n")
    
    return width, height, 1


def print_progress_bar(current_row, total_rows, bar_length=40):
    progress = (current_row + 1) / float(total_rows)
    filled = int(bar_length * progress)
    bar = "#" * filled + "-" * (bar_length - filled)
    percent = int(progress * 100)
    
    sys.stdout.write(f"\r[{bar}] {percent:3d}%")
    sys.stdout.flush()
    
    if current_row + 1 == total_rows:
        print()


def build_scene(rend: Renderer):
    env_map_name = None
    loaded_models = []
    
    try:
        env_map_name = "sky.jpg"
        rend.load_env_map(env_map_name, yaw_deg=0.0, vflip=False)
    except Exception:
        env_map_name = None
        
    grass = Material(
        diffuse=(0.35, 0.8, 0.35),
        ka=0.35,
        kd=0.9,
        ks=0.1,
        shininess=16,
        mat_type=OPAQUE,
        texture_path="grass.jpg",
    )
    
    mario_metal = Material(
        diffuse=(0.8, 0.8, 0.9),
        ka=0.15,
        kd=0.6,
        ks=1.0,
        shininess=256,
        mat_type=REFLECTIVE,
        reflectivity=0.8,
    )
    
    block_stone = Material(
        diffuse=(1.0, 1.0, 1.0),
        ka=0.8,
        kd=0.5,
        ks=0.15,
        shininess=32,
        mat_type=OPAQUE,
        texture_path="block.jpg",
        tex_brightness=2.0,
        emissive=(0.22, 0.20, 0.05),
    )
    
    trunk_mat = Material(
        diffuse=(0.4, 0.25, 0.1),
        ka=0.25,
        kd=0.85,
        ks=0.2,
        shininess=24,
        mat_type=OPAQUE,
    )
    
    leaves_mat = Material(
        diffuse=(0.25, 0.75, 0.22),
        ka=0.35,
        kd=0.95,
        ks=0.2,
        shininess=12,
        mat_type=OPAQUE,
    )
    
    pillar_wood = Material(
        diffuse=(0.6, 0.45, 0.25),
        ka=0.3,
        kd=0.85,
        ks=0.25,
        shininess=24,
        mat_type=OPAQUE,
        texture_path="wood.jpg",
    )
    
    ground = Plane(
        position=(0.0, -0.9, 0.0),
        normal=(0.0, 1.0, 0.0),
        material=grass,
        tex_scale=0.25,
    )
    rend.add_object(ground)
    
    try:
        obj_base = Material(
            diffuse=(1.0, 1.0, 1.0),
            ka=0.2,
            kd=0.9,
            ks=0.1,
            shininess=32,
            mat_type=OPAQUE,
        )
        star_tris = load_obj_as_triangles(
            "star.obj",
            obj_base,
            scale=0.4,
            translate=(0.0, -0.1, -2.0),
        )
        for tri in star_tris:
            rend.add_object(tri)
        loaded_models.append("star.obj")
    except Exception:
        pass
        
    try:
        mario_tris = load_obj_as_triangles(
            "mario.obj",
            mario_metal,
            scale=11,
            translate=(0.0, -0.6, -14.0),
        )
        for tri in mario_tris:
            rend.add_object(tri)
        loaded_models.append("mario.obj")
    except Exception:
        pass
        
    def add_tree(cx, cz, scale=1.0):
        trunk_height = 1.6 * scale
        trunk_radius = 0.18 * scale
        crown_radius = 0.55 * scale
        
        trunk_center = (cx, -1.0, cz)
        trunk = Cylinder(
            center=trunk_center,
            axis=(0.0, 1.0, 0.0),
            radius=trunk_radius,
            height=trunk_height,
            material=trunk_mat,
        )
        
        top_of_trunk_y = -1.0 + trunk_height
        crown_y = top_of_trunk_y + crown_radius * -0.9
        
        crown_left = Sphere(
            position=(cx - crown_radius * 0.9, crown_y, cz),
            radius=crown_radius,
            material=leaves_mat,
        )
        crown_right = Sphere(
            position=(cx + crown_radius * 0.9, crown_y, cz),
            radius=crown_radius,
            material=leaves_mat,
        )
        crown_top = Sphere(
            position=(cx, crown_y + crown_radius * 0.9, cz),
            radius=crown_radius,
            material=leaves_mat,
        )
        
        rend.add_object(trunk)
        rend.add_object(crown_left)
        rend.add_object(crown_right)
        rend.add_object(crown_top)
        
    def add_block(cx, cy, cz, sx, sy, sz):
        block = AABB(
            position=(cx, cy, cz),
            sizes=(sx, sy, sz),
            material=block_stone,
        )
        rend.add_object(block)
        
    def add_pillar(cx, cz, height=1.2, radius=0.12):
        pillar = Cylinder(
            center=(cx, -1.0, cz),
            axis=(0.0, 1.0, 0.0),
            radius=radius,
            height=height,
            material=pillar_wood,
        )
        rend.add_object(pillar)
        
    z_back = -12
    z_front = -6
    
    add_tree(-12, z_back, scale=1.6)
    add_tree(-9, z_back, scale=1.2)
    add_tree(-6, z_back, scale=1.6)
    add_tree(-6.6, z_front, scale=0.9)
    add_tree(-4.6, z_front, scale=0.9)
    add_tree(-4.5, z_front + 2, scale=0.54)
    
    base_z = -9.0
    base_x = 5.5
    step_x = 1.7
    
    add_block(base_x, -0.3, base_z + 0.05, 1.0, 1.0, 0.95)
    
    col2_x = base_x + step_x
    add_block(col2_x, -0.3, base_z - 0.1, 1.0, 1.0, 1.0)
    add_block(col2_x - 0.12, 0.7, base_z - 0.25, 0.95, 1.0, 0.9)
    
    col3_x = base_x + 2 * step_x
    add_block(col3_x, -0.3, base_z, 1.0, 1.0, 1.0)
    add_block(col3_x + 0.10, 0.7, base_z + 0.15, 0.96, 1.0, 0.95)
    add_block(col3_x - 0.15, 1.7, base_z + 0.30, 0.9, 1.0, 0.9)
    
    add_pillar(-3.8, -2.0, height=1.2, radius=0.22)
    add_pillar(-1.5, -3.3, height=1.25, radius=0.22)
    add_pillar(1.5, -3.3, height=1.25, radius=0.22)
    add_pillar(3.8, -2.0, height=1.2, radius=0.22)
    
    rend.add_light(AmbientLight(color=(1.0, 1.0, 1.0), intensity=0.32))
    rend.add_light(
        DirectionalLight(
            color=(1.0, 0.98, 0.94),
            intensity=1.15,
            direction=(-0.35, -1.0, -0.4),
        )
    )
    rend.add_light(
        PointLight(
            color=(1.0, 0.95, 0.9),
            intensity=0.8,
            position=(0.0, 2.0, 2.0),
            range_dist=25.0,
        )
    )
    
    return env_map_name, loaded_models


def main():
    final_width, final_height, final_ssaa = choose_resolution()
    
    rend = Renderer(
        final_width,
        final_height,
        fov=55,
        bg_color=(0.0, 0.0, 0.0),
        ssaa=final_ssaa,
    )
    
    rend.cam_pos = np.array((0.0, 1.4, 3.2), dtype=float)
    
    env_map_name, loaded_models = build_scene(rend)
    
    print(f"Environment Map: {env_map_name if env_map_name else '.jpg/.png'}")
    
    if not loaded_models:
        print("Modelo: .obj")
        print("Modelo: .obj")
    elif len(loaded_models) == 1:
        print(f"Modelo: {loaded_models[0]}")
        print("Modelo: .obj")
    else:
        print(f"Modelo: {loaded_models[0]}")
        print(f"Modelo: {loaded_models[1]}")
        
    print(f"Objetos en Escena: {len(rend.objects)}")
    print(f"Luces en Escena: {len(rend.lights)}")
    print()
    
    total_rows = final_height
    print("BARRA DE PROGRESO")
    
    def row_callback(j):
        print_progress_bar(j, total_rows)
        
    start_time = time.time()
    rend.render(row_callback=row_callback)
    render_time = time.time() - start_time
    
    print()
    print(f"TIEMPO RENDERIZADO: {render_time:0.2f} segundos")
    print()
    
    output_path = "Mario64.bmp"
    rend.save_bmp(output_path)
    print(f"Escena: {output_path}")


if __name__ == "__main__":
    main()