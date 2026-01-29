# HORSE Pre-Processing Deployment Guide

This document provides comprehensive instructions for deploying and configuring the HORSE Pre-Processing service.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Configuration Modes](#configuration-modes)
- [Deployment Script Usage](#deployment-script-usage)
- [Deployment Parameters](#deployment-parameters)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [Manual Deployment](#manual-deployment)

---

## Overview

The HORSE Pre-Processing service queries Elasticsearch for network traffic data and processes it for analysis. It supports three operational modes:
- **Static Mode**: Reads from pre-defined JSON data files
- **Live Data Mode**: Queries Elasticsearch in real-time using current timestamps
- **Time Range Mode**: Iterates through a specified historical time range

---

## Prerequisites

- **Docker & Docker Compose** installed
- **Bash** shell (Linux/macOS) or **Git Bash/WSL** (Windows)
- Access to the appropriate testbed network (CNIT/UMU/UPC)
- Valid Elasticsearch credentials

---

## Configuration Modes

### 1. Static Mode
```bash
STATIC_MODE=true
```
- Reads data from static JSON files (e.g., `demo_10_DDOS_values.json`, `demo_10_apiEXP_values.json`)
- Useful for demos and testing without live Elasticsearch
- Iterates through pre-defined data rows on each polling cycle

### 2. Live Data Mode
```bash
STATIC_MODE=false
LIVE_DATA=true
```
- Queries Elasticsearch in real-time
- Each query retrieves data from `now - POLLING_INTERVAL` to `now`
- Best for monitoring live network traffic
- `ES_DATA_START_TIME` and `ES_DATA_END_TIME` are automatically cleared

### 3. Time Range Mode
```bash
STATIC_MODE=false
LIVE_DATA=false
ES_DATA_START_TIME=2025-12-16T12:28:32.176Z
ES_DATA_END_TIME=2025-12-16T12:40:40.072Z
```
- Iterates through a specified historical time range
- Useful for replaying past events or analyzing specific time periods
- Increments by `POLLING_INTERVAL` on each iteration
- Stops when reaching `ES_DATA_END_TIME`

---

## Deployment Script Usage

The `deploy.sh` script simplifies deployment by automatically configuring environment variables and deploying with Docker Compose.

### Basic Syntax
```bash
./deploy.sh [OPTIONS]
```

### Script Actions
1. Parses command-line arguments
2. Updates `.env` file with specified configuration
3. Sets appropriate endpoints based on deployment domain
4. Stops existing Docker containers
5. Builds and starts new containers with updated configuration
6. Displays current configuration settings

---

## Deployment Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `--demo` | `10` | Specifies the demo number (currently only Demo 10 is configured) |
| `--demo_mode` | `api_exposure`, `ddos` | Sets the attack scenario type |
| `--static_mode` | `true`, `false` | Enables/disables static data mode |
| `--live_data` | `true`, `false` | Enables/disables live real-time querying |
| `--deployment_domain` | `CNIT`, `UMU`, `UPC` | Sets testbed-specific endpoints |
| `--ES_DATA_START_TIME` | ISO 8601 timestamp | Start time for time-range mode |
| `--ES_DATA_END_TIME` | ISO 8601 timestamp | End time for time-range mode |

### Demo Mode Details

When `--demo 10` is specified:
- **api_exposure**: 
  - `CONFIG_FILE_PATH=./config_demo10.json`
  - `STATIC_DATA_FILE_PATH=demo_10_apiEXP_values.json`
- **ddos**:
  - `CONFIG_FILE_PATH=./config_demo10.json`
  - `STATIC_DATA_FILE_PATH=demo_10_DDOS_values.json`

### Deployment Domain Details

| Domain | Elasticsearch URL | DEME URL |
|--------|-------------------|----------|
| **CNIT** | `http://192.168.130.48:9200` | `http://192.168.130.110:8090/estimate` |
| **UMU** | `http://127.0.0.1:9200` | `http://127.0.0.1:8090/estimate` |
| **UPC** | `http://10.19.2.15:9200` | `http://10.19.2.16:8090/estimate` |

---

## Usage Examples

### Example 1: Live Data Mode on CNIT Testbed (API Exposure)
Deploy in real-time monitoring mode for API exposure detection on CNIT testbed:
```bash
./deploy.sh --demo 10 --demo_mode api_exposure --deployment_domain CNIT --static_mode false --live_data true
```

### Example 2: Live Data Mode on UMU Testbed (DDoS)
Monitor for DDoS attacks in real-time on UMU testbed:
```bash
./deploy.sh --demo 10 --demo_mode ddos --deployment_domain UMU --static_mode false --live_data true
```

### Example 3: Time Range Replay on UPC Testbed
Replay historical data from a specific time range on UPC testbed:
```bash
./deploy.sh --demo 10 --demo_mode api_exposure --deployment_domain UPC --static_mode false --live_data false --ES_DATA_START_TIME "2025-12-16T12:28:32.176Z" --ES_DATA_END_TIME "2025-12-16T12:40:40.072Z"
```

### Example 4: Static Data Demo (DDoS)
Run a demo using pre-recorded static data:
```bash
./deploy.sh --demo 10 --demo_mode ddos --static_mode true
```

### Example 5: Quick Switch to Live Mode
Quickly switch the current deployment to live data mode:
```bash
./deploy.sh --live_data true
```

### Example 6: Change Deployment Domain Only
Switch to a different testbed without changing other settings:
```bash
./deploy.sh --deployment_domain CNIT
```

### Example 7: Full Configuration
Complete deployment with all parameters specified:
```bash
./deploy.sh \
  --demo 10 \
  --demo_mode api_exposure \
  --deployment_domain CNIT \
  --static_mode false \
  --live_data false \
  --ES_DATA_START_TIME "2025-12-16T12:28:32.176Z" \
  --ES_DATA_END_TIME "2025-12-16T12:40:40.072Z"
```

---

## Environment Variables

The following environment variables are configured in the `.env` file:

### Elasticsearch Configuration
- `ES_USERNAME`: Elasticsearch username (default: `elastic`)
- `ES_PASSWORD`: Elasticsearch password
- `ES_INDEX`: Index to query (default: `holo_demo_data_api`)
- `ES_ANALYTICS_INDEX`: Analytics index name
- `ES_URL`: Elasticsearch endpoint URL

### Application Configuration
- `STATIC_MODE`: Enable/disable static data mode (`true`/`false`)
- `LIVE_DATA`: Enable/disable live real-time mode (`true`/`false`)
- `CONFIG_FILE_PATH`: Path to query configuration file
- `STATIC_DATA_FILE_PATH`: Path to static data JSON file
- `POLLING_INTERVAL`: Query interval in seconds (default: `120`)

### Time Range Configuration
- `ES_DATA_START_TIME`: Start timestamp for time-range mode (ISO 8601 format)
- `ES_DATA_END_TIME`: End timestamp for time-range mode (ISO 8601 format)

### Endpoint Configuration
- `AFTER_PRE_PROCESSING_URL`: URL for posting processed results (DEME endpoint)

---

## Manual Deployment

If you prefer not to use the deployment script, you can manually deploy:

### 1. Edit the `.env` file
```bash
nano .env
```

### 2. Set your desired configuration
Example for live data mode:
```properties
STATIC_MODE=false
LIVE_DATA=true
CONFIG_FILE_PATH=./config_demo10.json
STATIC_DATA_FILE_PATH=demo_10_DDOS_values.json
POLLING_INTERVAL=120
ES_DATA_START_TIME=
ES_DATA_END_TIME=
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
```

### 3. Deploy with Docker Compose
```bash
docker-compose down
docker-compose up --build -d
```

### 4. View logs
```bash
docker-compose logs -f
```

### 5. Stop the service
```bash
docker-compose down
```

---

## Monitoring and Troubleshooting

### View Real-Time Logs
```bash
docker-compose logs -f
```

### View Container Status
```bash
docker-compose ps
```

### Restart the Service
```bash
docker-compose restart
```

### Check Current Configuration
After deployment, the script displays current settings:
```
Configuration updated. Current settings:
-------------------------------------------
CONFIG_FILE_PATH=./config_demo10.json
STATIC_DATA_FILE_PATH=demo_10_DDOS_values.json
STATIC_MODE=false
LIVE_DATA=true
ES_DATA_START_TIME=
ES_DATA_END_TIME=
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
-------------------------------------------
```

### Common Issues

**Issue: "No data being retrieved"**
- Check Elasticsearch connectivity: `curl http://<ES_URL>`
- Verify credentials in `.env`
- Ensure the specified index exists
- Check time range settings (if using time-range mode)

**Issue: "Docker containers not starting"**
- Check Docker daemon: `docker ps`
- Review logs: `docker-compose logs`
- Verify port 5001 is not already in use

**Issue: "Static data not loading"**
- Verify JSON file path in `STATIC_DATA_FILE_PATH`
- Check JSON file format and structure
- Ensure file is in the `app/` directory

---

## Port Configuration

The service exposes port **5001** on the host, mapped to port **5000** in the container:
```
ports:
  - "5001:5000"
```

To change the host port, edit `docker-compose.yml`.

---

## Additional Notes

- The deployment script uses `sed` to update `.env` file, which works on Linux/macOS/Git Bash
- On Windows without Git Bash, consider using WSL or manually editing `.env`
- All timestamps should be in ISO 8601 format with 'Z' suffix or timezone offset
- The `POLLING_INTERVAL` determines how frequently queries are executed (in seconds)
- When `LIVE_DATA=true`, time range parameters are automatically cleared to avoid conflicts

---

## Support

For issues or questions, please refer to the HORSE project documentation or contact the development team.
