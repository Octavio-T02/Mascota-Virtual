<div align="center">

# 🐾 Uni The Cat

### Pixel Art Desktop Pet

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![MPRIS](https://img.shields.io/badge/MPRIS-Supported-ff9ebb?style=for-the-badge)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

<p>Una mascota de escritorio en pixel art procedural para Linux, desarrollada en Python y PyQt6.</p>

</div>

## ✨ Características

* 🎨 **Renderizado 100% Procedural**: No requiere archivos PNG externos; todo el sprite y sus animaciones (caminar, comer, dormir, bailar, arrastrar) se dibujan píxel por píxel mediante matrices dinámicas en `QPainter`.
* ✨ **Sistema de Partículas Pixel Art**: Generación de corazones (`♥`), símbolos de sueño (`z`), migajas (`.`) y notas musicales (`♫`).
* ♫ **Detección de Música (MPRIS)**: Rastrea reproducciones de Spotify o navegadores con `playerctl` para activar automáticamente el estado *DANCE* y mostrar la canción en un globo de texto.
* ▲ **Salto a Ventana Activa**: Detecta la ubicación de la ventana enfocada mediante `xdotool` y se posiciona justo arriba del borde superior.
* 🍗 **Sistema de Estadísticas (Tamagotchi)**:
  * **Hambre**: Requiere panecillos para mantenerse lleno.
  * **Energía**: Disminuye con el tiempo y se recupera mandándolo a dormir.
  * **Felicidad**: Aumenta al acariciar sus mofletes.
* 🔒 **Persistencia y Fijación**: Permite arrastrar la mascota libremente o fijarla en pantalla. La posición y estado se guardan automáticamente con `QSettings`.
* 🌸 **Interfaz Kawaii / Pastel**: Menú contextual estilizado con paleta de colores suave.

---

## 🛠️ Requisitos e Instalación

### 1. Dependencias del Sistema (Linux)

Asegúrate de instalar `playerctl` (para rastrear música) y `xdotool` (para la detección de ventanas):

```bash
sudo apt update
sudo apt install playerctl xdotool
