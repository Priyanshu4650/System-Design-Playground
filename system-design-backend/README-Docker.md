# Load Testing Backend - Docker Setup

## Quick Start

### Option 1: Using Docker Compose (Recommended)
```bash
# Build and run the container
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the container
docker-compose down
```

### Option 2: Using Docker directly
```bash
# Build the image
docker build -t load-test-backend .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data load-test-backend

# Run in background
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name load-test-backend load-test-backend
```

## Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Data Persistence

The SQLite database is stored in the `./data` directory and persists between container restarts.

## API Endpoints

### Load Testing
- `POST /v1/tests/start` - Start a load test
- `GET /v1/tests/{test_id}/result` - Get test results
- `GET /v1/tests/{test_id}/download` - Download results as JSON
- `POST /v1/tests/{test_id}/email` - Email results

### Visit Tracking
- `POST /v1/visits/track` - Track page visit
- `GET /v1/visits/stats` - Get visit statistics
- `GET /v1/visits/admin?password=admin123` - Admin statistics
- `GET /v1/visits/admin/download?password=admin123` - Download database

## Container Management

```bash
# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Remove container and data
docker-compose down -v
rm -rf data/

# Rebuild after code changes
docker-compose up --build
```