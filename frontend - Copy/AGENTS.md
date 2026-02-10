## Project Summary
Velora is a premium fleet route optimization platform designed for complex logistics. It allows users to upload vehicle and request data via Excel, processes optimizations, and provides detailed metrics, route visualizations, and employee-specific results.

## Tech Stack
- Frontend: React (Vite)
- Animations: Framer Motion
- Icons: Lucide React
- Maps: Leaflet / React-Leaflet
- Data Parsing: XLSX

## Architecture
- `App.jsx`: Main state orchestrator (Home, Upload Workflow, Results).
- `components/`: Modular UI components.
- `api.js`: Handles communication with the optimization backend.
- `excelParser.js`: Processes client-side Excel files.

## User Preferences
- **Aesthetic**: Modern, dynamic, "best looking" UI.
- **Theme**: Dark mode by default with vibrant accents (Electric Blue, Vivid Violet).
- **Interactivity**: High-impact animations and staggered reveals.
- **Design System**: Glassmorphism, premium typography, and sharp alignments.

## Project Guidelines
- Do NOT modify `api.js`.
- Use functional components and modern React patterns.
- Prefer CSS variables for styling.
- Minimize technical jargon for non-technical users.

## Common Patterns
- Framer Motion for entrance animations.
- Lucide icons for visual context.
- Glassmorphism containers (`backdrop-filter: blur`).
