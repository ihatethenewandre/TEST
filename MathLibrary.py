import numpy as np


def normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    
    if norm == 0:
        return v
        
    return v / norm


def clamp_01(x):
    if x < 0.0:
        return 0.0
        
    if x > 1.0:
        return 1.0
        
    return x


def reflect_vector(normal, direction):
    normal = normalize(normal)
    direction = normalize(direction)
    
    reflect = 2.0 * np.dot(normal, direction) * normal - direction
    
    return normalize(reflect)