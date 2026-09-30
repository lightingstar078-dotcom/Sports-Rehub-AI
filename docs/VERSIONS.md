# Version choices checked 2026-09-30

Frontend package versions used by this prototype:
- React 19.3.0
- Vite 8.3.1
- TypeScript 7.0.2
- Tailwind CSS 4.3.3
- @tailwindcss/vite 4.3.3
- vite-plugin-pwa 1.3.0
- @mediapipe/tasks-vision 1.0.1
- Zustand 5.0.15
- Recharts 3.10.1
- Lucide React 1.48.0
- @vitejs/plugin-react 6.1.1

Backend requirement ranges intentionally allow patch updates within major/minor compatibility windows.

The external MediaPipe model asset is not bundled. The backend verifies its presence before pose analysis.
