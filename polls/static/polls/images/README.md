# Knowledge Garden Assets

This folder contains all the visual assets for the Knowledge Garden feature.

## Required Files

### 1. **greenhouse-background.png**
- **Size**: 900x700px (or larger)
- **Description**: Cozy greenhouse interior background
- **Style**: Pixel art with warm wooden structure, glass windows, blue sky
- **Details**: Should have a clear center area for the 3x3 plant grid
- **Colors**: Warm browns (#8B4513), sky blues (#87CEEB), greens
- **Fallback**: If missing, a gradient background will be used

### 2. **seed-packet.png**
- **Size**: 48x48px (or 64x64px)
- **Description**: Draggable seed packet icon for sidebar
- **Style**: Brown paper bag with torn top, small plant sketch
- **Fallback**: If missing, 🌱 emoji will be shown

### 3. **water-can.png**
- **Size**: 80x80px (or 100x100px)
- **Description**: Watering can icon for the water meter
- **Style**: Classic metal watering can, pixel art
- **Colors**: Metallic gray or green
- **Fallback**: If missing, 💧 emoji will be shown

## Folder Structure

```
images/
├── README.md (this file)
├── greenhouse-background.png
├── seed-packet.png
├── water-can.png
└── plants/
    ├── README.md
    ├── plant-stage-0.png
    ├── plant-stage-1.png
    ├── plant-stage-2.png
    ├── plant-stage-3.png
    ├── plant-stage-4.png
    └── plant-stage-5.png
```

## Design Style Guide

**Theme**: Cozy pixel-art greenhouse garden (Stardew Valley aesthetic)

**Color Palette**:
- Greenhouse wood: `#8B4513` (saddle brown)
- Sky: `#87CEEB` (sky blue)
- Grass/Plants: `#6B8E23` to `#228B22`
- Water: `#4FC3F7` to `#81D4FA` (cyan/light blue)
- Soil: `#3E2723` (dark brown)
- Pots: `#CD853F` (terracotta orange)
- Flowers: Pink `#FF69B4`, Yellow `#FFD700`, Purple `#9370DB`

## Getting Started Without Assets

The system is fully functional even without custom images:
- Greenhouse shows a gradient background
- Seed packet shows 🌱 emoji
- Water can shows 💧 emoji
- Plants show emoji progression: 🪴 → 🌱 → 🌿 → ☘️ → 🪴 → 🌸

Add your custom pixel art assets to see them in action!

## AI Image Generation Prompts

See the main design brief document for detailed AI prompts for generating these assets.
