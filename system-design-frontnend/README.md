# System Design Playground Frontend

Load testing dashboard built with React, TypeScript, and Vite.

## GitHub Pages Deployment

### Automatic Deployment
1. Push to `main` branch
2. GitHub Actions will automatically build and deploy to GitHub Pages
3. Site will be available at: `https://[username].github.io/System-Design-Playground/`

### Manual Deployment
```bash
cd system-design-frontnend
npm install
npm run build
```

### Configuration
- **Backend API**: Configured to use Render deployment
- **Base Path**: Set for GitHub Pages (`/System-Design-Playground/`)
- **Build Output**: `dist/` directory

### Features
- Load test configuration
- Real-time results dashboard
- Charts and metrics visualization
- Visit tracking

### Local Development
```bash
cd system-design-frontnend
npm install
npm run dev
```

Open http://localhost:5173