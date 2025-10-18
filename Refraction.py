import numpy as np
from math import acos, asin


def refract_vector(normal, incident, n1, n2):
    c1 = np.dot(normal, incident)
    
    if c1 < 0:
        c1 = -c1
    else:
        normal = np.array(normal) * -1
        n1, n2 = n2, n1
        
    n = n1 / n2
    term = 1 - n ** 2 * (1 - c1 ** 2)
    
    if term < 0:
        return None
        
    t_vec = n * (incident + c1 * normal) - normal * term ** 0.5
    
    return t_vec / np.linalg.norm(t_vec)


def total_internal_reflection(normal, incident, n1, n2):
    c1 = np.dot(normal, incident)
    
    if c1 < 0:
        c1 = -c1
    else:
        n1, n2 = n2, n1
        
    if n1 < n2:
        return False
        
    theta1 = acos(c1)
    
    try:
        theta_c = asin(n2 / n1)
        return theta1 >= theta_c
    except ValueError:
        return True


def fresnel(normal, incident, n1, n2):
    c1 = np.dot(normal, incident)
    
    if c1 < 0:
        c1 = -c1
    else:
        n1, n2 = n2, n1
        
    s2 = (n1 * (1 - c1 ** 2) ** 0.5) / n2
    c2 = (1 - s2 ** 2) ** 0.5
    
    f1 = (((n2 * c1) - (n1 * c2)) / ((n2 * c1) + (n1 * c2))) ** 2
    f2 = (((n1 * c2) - (n2 * c1)) / ((n1 * c2) + (n2 * c1))) ** 2
    
    kr = (f1 + f2) / 2
    kt = 1 - kr
    
    return kr, kt