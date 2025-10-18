class Intercept(object):
    def __init__(self, point, normal, distance, ray_direction, obj, uv=None):
        self.point = point
        self.normal = normal
        self.distance = distance
        self.ray_direction = ray_direction
        self.obj = obj
        self.uv = uv