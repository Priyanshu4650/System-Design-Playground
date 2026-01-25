# Load Testing Frontend

A production-ready React + TypeScript frontend for the backend-driven load testing system.

## Features

### ✅ Test Configuration Form
- **Test Modes**: Total requests OR RPS + Duration
- **Concurrency Control**: Configurable max in-flight requests (1-1000)
- **Feature Toggles**: Idempotency, Retries, Failure Injection
- **Failure Injection Settings**: DB latency slider, failure rate percentage, timeout configuration
- **Client-side Validation**: TypeScript + form validation with error messages

### ✅ Professional Results Dashboard
- **Summary Cards**: Total requests, success rate, failures, duration
- **Latency Panel**: Average, P95, P99 latency metrics
- **Interactive Charts**: 
  - Pie chart for request status distribution
  - Bar chart for latency percentiles
- **Detailed Table**: Complete statistics grid
- **Real-time Updates**: Auto-refresh toggle with status monitoring

### ✅ Production Architecture
- **Strict TypeScript**: Full type safety for all API interactions
- **API Service Layer**: Typed functions with error handling
- **Custom Hooks**: `useTestRunner()` for business logic separation
- **React Query**: Caching, background updates, error handling
- **Clean Component Structure**: Separation of concerns

## Tech Stack

- **React 19** + **TypeScript**
- **@tanstack/react-query** - Data fetching and caching
- **Recharts** - Interactive charts and visualizations
- **Inline CSS** - Component-scoped styling
- **Vite** - Build tool and dev server

## Project Structure

```
src/
├── App.tsx                 # Main app with QueryClient provider
├── types.ts               # TypeScript interfaces for API
├── api.ts                 # API service layer with typed functions
├── useTestRunner.ts       # Custom hook for test logic
├── TestConfigForm.tsx     # Configuration form component
├── ResultsDashboard.tsx   # Results display component
├── Charts.tsx             # Chart components using Recharts
├── examples.json          # Example API payloads
├── styles.css            # Global styles
└── main.tsx              # App entry point
```

## Installation & Setup

1. **Install Dependencies**
```bash
npm install
```

2. **Start Development Server**
```bash
npm run dev
```

3. **Build for Production**
```bash
npm run build
```

## API Integration

The frontend expects these backend endpoints:

### Start Test
```
POST /v1/tests/start
Content-Type: application/json

{
  "config": {
    "total_requests": 1000,
    "concurrency_limit": 50,
    "retries_enabled": true,
    "idempotency_enabled": true,
    "failure_injection": {
      "enabled": true,
      "failure_rate": 0.05
    }
  }
}
```

### Get Results
```
GET /v1/tests/{test_id}/result

Response: {
  "test_id": "uuid",
  "status": "completed",
  "total_requests": 1000,
  "succeeded": 950,
  "failed": 30,
  "avg_latency_ms": 125.5,
  "p95_latency_ms": 280.0,
  "p99_latency_ms": 450.0
}
```

### Get Status (Optional)
```
GET /v1/tests/{test_id}/status

Response: {
  "test_id": "uuid",
  "status": "running",
  "progress": { "message": "Test is running" }
}
```

## Component Details

### TestConfigForm
- Form validation with TypeScript
- Dynamic UI based on test mode selection
- Failure injection settings with sliders
- Real-time validation feedback

### ResultsDashboard
- Loading states and error handling
- Auto-refresh functionality
- Professional summary cards
- Interactive charts with Recharts
- Detailed statistics table

### Charts
- Pie chart for status distribution with custom colors
- Bar chart for latency percentiles
- Responsive design with proper legends
- Handles empty data states

### useTestRunner Hook
- Manages test lifecycle state
- React Query integration for caching
- Auto-refresh logic for running tests
- Error handling and retry logic

## Configuration Options

### Test Modes
```typescript
// Total Requests Mode
{
  total_requests: 1000,
  concurrency_limit: 50
}

// RPS + Duration Mode  
{
  rps: 10,
  duration_sec: 60,
  concurrency_limit: 25
}
```

### Feature Toggles
```typescript
{
  enable_idempotency: boolean,
  enable_retries: boolean,
  enable_failure_injection: boolean
}
```

### Failure Injection
```typescript
{
  failure_injection: {
    db_latency_ms: 50,      // 10-1000ms slider
    failure_rate: 5,        // 0-100% slider  
    timeout_ms: 5000        // Input field
  }
}
```

## State Management

### React Query Configuration
- 1 retry on failure
- No refetch on window focus
- 2-second intervals for auto-refresh
- Automatic cache invalidation

### Local State
- Form configuration state
- Test ID tracking
- Auto-refresh toggle
- Error states

## Error Handling

### API Errors
- Network failures with retry options
- Invalid test ID (404) handling
- Server errors (500) with user-friendly messages

### Form Validation
- Required field validation
- Range validation (concurrency 1-1000)
- Conditional validation (RPS mode requires both RPS and duration)

### Loading States
- Button disabled states during API calls
- Loading spinners for data fetching
- Skeleton states for charts

## Responsive Design

- **Desktop First**: Optimized for dashboard usage
- **Grid Layout**: Responsive configuration and results panels
- **Mobile Friendly**: Stacked layout on smaller screens
- **Chart Responsiveness**: Recharts responsive containers

## Performance Optimizations

- **React Query Caching**: Prevents unnecessary API calls
- **Conditional Rendering**: Charts only render with data
- **Memoized Calculations**: Success rates and formatting
- **Efficient Re-renders**: Proper dependency arrays

## Production Considerations

### Type Safety
- Strict TypeScript configuration
- API response type validation
- Form input type checking

### Error Boundaries
- Graceful error handling
- User-friendly error messages
- Retry mechanisms

### Accessibility
- Semantic HTML structure
- Proper form labels
- Color contrast compliance
- Keyboard navigation support

## Example Usage

1. **Configure Test**
   - Select "Total Requests" mode
   - Set 1000 requests, 50 concurrency
   - Enable failure injection with 5% failure rate

2. **Start Test**
   - Click "Start Test" button
   - Test ID appears in status bar
   - Auto-refresh begins

3. **Monitor Progress**
   - Watch real-time status updates
   - Toggle auto-refresh as needed
   - View progress messages

4. **Analyze Results**
   - Review summary cards
   - Examine latency metrics
   - Analyze distribution charts
   - Export detailed statistics

## Development

### Code Quality
- ESLint configuration
- TypeScript strict mode
- Component separation
- Clean architecture patterns

### Testing Strategy
- Type checking with TypeScript
- API integration testing
- Component unit tests
- E2E testing scenarios

This frontend provides a complete, production-ready interface for load testing with professional UX, comprehensive error handling, and real-time monitoring capabilities.