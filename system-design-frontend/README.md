# System Design Control Plane UI

Production-grade React + TypeScript control plane for distributed backend system testing and observability.

## Architecture

### Component Hierarchy
```
App
├── TrafficGenerator     - Manual/automated traffic generation
├── FailureToggles      - Backend failure injection controls  
├── MetricsCharts       - Real-time metrics visualization
└── RequestExplorer     - Request history with trace timeline
```

### State Management
- **Local Component State** - UI-specific state (forms, modals)
- **Custom Hooks** - Shared logic (WebSocket, API calls)
- **Context-free Design** - No global state, services handle data

### Real-Time Updates
- **WebSocket Primary** - Live metrics and request updates
- **Polling Fallback** - Graceful degradation when WS fails
- **Reconnection Logic** - Automatic reconnect with exponential backoff

## Key Features

### ✅ Traffic Generator UI
- **Single Request** - One-off API calls
- **Burst Mode** - N requests simultaneously  
- **Sustained Load** - RPS over time duration
- **Live Results** - Success/failure counts with request IDs

### ✅ Failure Toggles
- **Master Toggle** - Enable/disable all failure injection
- **Failure Rate Slider** - 0-100% failure probability
- **DB Latency Range** - Min/max artificial latency
- **Timeout Controls** - DB and Redis timeout settings
- **Backend Sync** - UI reflects actual backend state

### ✅ Metrics Charts  
- **Real-time Updates** - WebSocket + polling fallback
- **Key Metrics** - Request rate, error rate, retry count, P95/P99 latency
- **Mini Charts** - SVG line charts with current values
- **Connection Status** - Live/polling indicator

### ✅ Request Explorer
- **Recent Requests Table** - Last 50 requests with status/latency
- **Trace Timeline** - Click row to see detailed event timeline
- **Failure Highlighting** - Visual indicators for errors/retries
- **Real-time Updates** - New requests appear automatically

## Usage

### Development
```bash
npm install
npm start
```

### Production Build
```bash
npm run build
```

### Environment Variables
```bash
REACT_APP_API_BASE=http://localhost:8000
```

## API Integration

The UI expects these backend endpoints:
- `POST /v1/traffic/generate` - Traffic generation
- `GET/PUT /v1/config/failure` - Failure configuration
- `GET /metrics/json` - Metrics data
- `GET /v1/requests/recent` - Request history
- `GET /v1/trace/{id}` - Request traces
- `WS /ws` - Real-time updates

See `API_CONTRACTS.md` for detailed schemas.

## Incident Response Features

### Emergency Controls
- **Emergency Stop Button** - Immediately halt all traffic
- **Failure State Visibility** - Red indicators for active failures
- **Connection Monitoring** - Backend/WebSocket status indicators

### Observability
- **Request Correlation** - Click any request to see full trace
- **Failure Analysis** - Separate views for failures vs retries
- **Performance Monitoring** - P95/P99 latency tracking

### Production Considerations
- **Graceful Degradation** - Works without WebSocket
- **Error Boundaries** - Component-level error handling
- **Type Safety** - Strict TypeScript for all API contracts
- **Responsive Design** - Mobile-friendly incident response

## File Structure
```
src/
├── components/          # React components
│   ├── TrafficGenerator.tsx
│   ├── FailureToggles.tsx  
│   ├── MetricsCharts.tsx
│   └── RequestExplorer.tsx
├── hooks/              # Custom hooks
│   └── useWebSocket.ts
├── services/           # API services
│   └── api.ts
├── types/              # TypeScript types
│   └── api.ts
└── App.tsx            # Main application
```

This control plane is designed for production incident response with clear visual separation between traffic control, failure injection, and observability.