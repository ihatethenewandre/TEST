# Proyecto II — Gráficas por Computadora

**Universidad del Valle de Guatemala** **Autor:** André Pivaral  
**Fecha:** 15 de Octubre de 2025

---

## Descripción

Este proyecto consiste en la implementación de un **Ray Tracer** completo escrito en Python. La escena renderizada recrea un nivel icónico inspirado en **Super Mario 64**.

La idea surgió al ver un video en YouTube de Super Mario 64 renderizado con tecnología moderna de Ray Tracing. Me di cuenta de que la geometría original del videojuego (basada principalmente en primitivas como esferas, cilindros y polígonos simples) es bastante accesible y se alinea perfectamente con los conocimientos adquiridos en el curso. Esto me permitió plantear el desafío de recrear esa estética nostálgica cumpliendo con todos los requisitos técnicos del proyecto. Además, al ser mi videojuego favorito, la motivación para cuidar los detalles y entregar un resultado de alta calidad fue personal.

El motor soporta materiales opacos, reflectivos, texturizados, manejo de luces (ambiental, direccional y puntual), sombras y carga de modelos OBJ complejos.

---

## Composición de la Escena

La escena está compuesta por los siguientes elementos geométricos y recursos:

* **Árboles (6 unidades):**
    * Cada árbol está compuesto por **1 Cilindro** (el tronco) y **3 Esferas** (el follaje).
* **Bloques de Piedra (5 unidades):**
    * Representados mediante figuras **AABB** (Axis Aligned Bounding Boxes) con texturas.
* **Pilares de Madera (4 unidades):**
    * Modelados utilizando **Cilindros** con texturas.
* **Suelo:**
    * **1 Plano** infinito con textura de pasto.
* **Modelos 3D (.obj):**
    * **Mario Metal:** Modelo complejo cargado mediante triángulos, utilizando un material altamente reflectivo (Metal Cap).
    * **Estrella (Star):** Modelo cargado mediante triángulos con material opaco.
* **Texturas Implementadas (4 texturas + Skybox):**
    * `sky.jpg` (Environment Map / Cielo).
    * `grass.jpg` (Suelo).
    * `block.jpg` (Bloques).
    * `wood.jpg` (Pilares).
* **Materiales:**
    * Se implementaron múltiples definiciones de materiales, incluyendo materiales mate, materiales con textura e iluminación especular (Phong), y materiales reflectivos (espejo).

---

## Comparación de Resultados

A la izquierda se muestra una imagen de referencia del estilo visual buscado, y a la derecha el render final obtenido (.bmp) con el Ray Tracer:

| Referencia (Inspiración) | Render Final (Ray Tracer) |
| :---: | :---: |
| <img src="image_10d819.jpg" alt="Referencia Mario 64" width="400"/> | <img src="Escena.bmp" alt="Render Final" width="400"/> |

---

## Enlace Repositorio

Branch: **Proyecto2** <https://github.com/ihatethenewandre/Graficas/tree/Proyecto2>

---

## Ejecución

1. **Clonar el Repositorio**
   ```bash
   # Clonar el Repositorio
   git clone [https://github.com/ihatethenewandre/Graficas.git](https://github.com/ihatethenewandre/Graficas.git)
   # Moverse al Repositorio
   cd Graficas
   # Moverse a la Branch correspondiente
   git switch Proyecto2
