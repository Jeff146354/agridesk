# Agridesk Frontend

Modern, premium Web Application for the Agridesk Academic Document Ledger. Built with a focus on fluid interactions, elegant aesthetics, and robust security.

## Technology Stack

- **Core**: React 18 + Vite (for instantaneous HMR and builds)
- **Styling**: Tailwind CSS v4 (configured with a custom Ivory/Sepia premium theme)
- **Animations**: Framer Motion (for fluid page transitions and micro-interactions)
- **Icons**: Lucide React
- **PDF Engine**: React-PDF + PDF.js (for secure, in-browser token-gated document streaming)
- **Interactions**: 
  - `@dnd-kit/core` (for drag-and-drop signature placement logic)
  - `react-dropzone` (for wizard-based document uploading)
- **Notifications**: Sonner (for elegant, stackable toast alerts)
- **Data Fetching**: Axios (configured with intercepts for JWT Auth handling)

## Key Features

- **Wizard-based Workflows**: Multi-step external document upload with interactive Drag-and-Drop signature placement.
- **In-App PDF Viewer**: Secure PDF viewing bypassing browser download managers and CORS blocks using token-authenticated Blob streaming.
- **Fluid UI/UX**: Premium animations across routing transitions, empty states, and dialogs.
- **Role-Based Views**: Context-aware dashboards tailored for `MAHASISWA`, `DOSEN`, and `ADMIN`.

## Getting Started

### Prerequisites

- Node.js (v18+)
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure Environment:
   Create a `.env` file (or use default configuration) to point to the backend API.
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. Start the Development Server:
   ```bash
   npm run dev
   ```

4. Build for Production:
   ```bash
   npm run build
   ```

## Development Rules

- **Theme & Styling**: Stick to the defined design system (Ivory background, muted Sepia accents) defined in Tailwind configuration. Avoid harsh primary colors.
- **Components**: Reuse shared UI components where possible.
- **State Management**: Use React Context for global auth state and localized `useState` for component-level UI state to keep the architecture clean and decoupled.
