# HORSE Pre-Processing Deployment Guide

This document provides comprehensive instructions for deploying and configuring the HORSE Pre-Processing service.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Configuration Modes](#configuration-modes)
- [Deployment Script Usage](#deployment-script-usage)
- [Deployment Parameters](#deployment-parameters)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [Manual Deployment](#manual-deployment)

---

## Overview

The HORSE Pre-Processing service is a flexible, configurable software system designed for creating and maintaining data streams from various sources. It serves as a critical middleware component that connects data sources (such as Elasticsearch) with downstream analysis and decision-making systems (such as DEME - Decision Making Engine).

### Purpose

This service enables continuous monitoring and processing of network traffic data, security events, and system metrics across distributed testbed environments. It provides a unified framework for querying, transforming, and dispatching data with configurable intervals and processing rules.

### Architecture

The system is built around three major architectural components that work together to provide end-to-end data stream management:

#### 1. Query Configuration Layer
**Purpose**: Defines *from where* to read data, *when* to query it, and *how* to structure the queries.

- **Configuration Files**: Stored in `data_queries_config/`, these JSON files define:
  - Source data location (Elasticsearch indices)
  - Query structure and aggregations (IP grouping, traffic counts, etc.)
  - Query type (`_search`, `_count`, etc.)
  - Polling intervals (how frequently to execute queries)
  - Time window specifications (historical ranges or real-time)
  
- **Flexible Querying**: Supports multiple query patterns:
  - Range queries with dynamic time windows
  - Aggregation-based analytics
  - Multi-field filtering and grouping
  
- **Subscription Management**: Each query configuration represents a data subscription with unique IDs, user associations, and activation status.

#### 2. Pre-Processing and Transformation Layer
**Purpose**: Defines *how* to process raw data and *how* to transform it for downstream consumption.

- **Data Processing**:
  - Extracts relevant metrics from Elasticsearch responses
  - Aggregates data by IP addresses, domains, or custom fields
  - Handles missing data and error conditions gracefully
  
- **Transformation Pipeline**:
  - Converts raw query results into standardized formats
  - Maps source-specific fields to target schema
  - Applies feature extraction (DNS counts, NTP traffic, NEF metrics, etc.)
  - Generates instance-based data structures with features and values
  
- **Multiple Processing Modes**:
  - **Static Mode**: Reads from pre-recorded JSON data files for demonstrations
  - **Live Mode**: Processes real-time data from active sources
  - **Time-Range Mode**: Iterates through historical data windows
  
- **Metadata-Driven**: Uses metadata specifications to determine:
  - Feature names and types
  - Value data types (int, float, string)
  - Timestamp formats (Unix, ISO 8601)
  - Instance naming conventions

#### 3. Data Dispatching Layer
**Purpose**: Defines *where* to send processed data, *how* to transmit it, and *at what intervals*.

- **Multi-Destination Support**:
  - **DEME API**: Sends transformed data to Decision Making Engine for analysis
  - **Analytics Index**: Stores processed results in Elasticsearch for historical analysis
  - Configurable endpoints per deployment domain (CNIT, UMU, UPC)
  
- **Transmission Protocol**:
  - RESTful API calls with JSON payloads
  - Authenticated connections with credentials management
  - Error handling and retry logic
  
- **Interval Control**:
  - Configurable polling intervals (default: 120 seconds)
  - Synchronized dispatching with query execution
  - Time-based triggering for batch processing
  
- **Payload Structure**:
  - Timestamp-stamped data points
  - Instance-oriented organization (nodes, systems, domains)
  - Feature-value pairs for each metric
  - Supports single and multi-instance payloads

### Operational Modes

The service supports three operational modes to accommodate different use cases:

- **Static Mode**: Reads from pre-defined JSON data files
  - Ideal for demonstrations, testing, and development
  - No live Elasticsearch connection required
  - Iterates through pre-recorded attack scenarios
  - **Default mode for all demos**

- **Live Data Mode**: Queries Elasticsearch in real-time using current timestamps
  - Monitors active network traffic and security events
  - Each query retrieves data from `now - POLLING_INTERVAL` to `now`
  - Best for production monitoring and real-time threat detection

- **Time Range Mode**: Iterates through a specified historical time range
  - Replays past events for analysis and validation
  - Increments by `POLLING_INTERVAL` on each iteration
  - Useful for post-incident analysis and testing

### Available Demo Scenarios

The service supports multiple demo scenarios, each demonstrating different attack patterns and monitoring capabilities:

- **Demo 5**: Multi-domain DNS attack scenario
  - Monitors 2 nodes across CNIT and UPC testbeds
  - Tracks DNS traffic patterns during coordinated attacks
  - 15 data points showing attack ramp-up and ramp-down
  - Demonstrates cross-testbed correlation

- **Demo 9**: Network Exposure Function (NEF) monitoring
  - Monitors 9 instances with NEF features
  - Uses pcap_data for packet-level analysis
  - Tracks network exposure patterns

- **Demo 10**: API Exposure and DDoS scenarios
  - Two modes: `api_exposure` and `ddos`
  - Monitors multiple endpoints for threat detection
  - Uses holo_demo_data_api index
  - Includes automatic testbed configuration

---

## Project Structure

The project is organized with a clear separation between query configurations and static demonstration data:

```
app/
├── data_queries_config/          # Elasticsearch query configurations
│   ├── config.json               # Default configuration
│   ├── config_demo_5.json        # Demo 5: Multi-domain DNS monitoring
│   ├── config_demo_9.json        # Demo 9: NEF monitoring
│   └── config_demo10.json        # Demo 10: API exposure and DDoS
│
├── static_data_config/           # Pre-recorded demo data
│   ├── demo_5_values.json        # Demo 5 static values
│   ├── demo_9_values.json        # Demo 9 static values
│   ├── demo_10_apiEXP_values.json    # Demo 10 API exposure values
│   └── demo_10_DDOS_values.json      # Demo 10 DDoS values
│
├── main.py                       # Application entry point
├── ES_queries.py                 # Query management class
└── elastic_query.py              # Elasticsearch query execution
```

### Configuration Files (`data_queries_config/`)
These JSON files define:
- Elasticsearch indices to query
- Query structure and aggregations
- Subscription IDs and user information
- Query intervals and activation status

### Static Data Files (`static_data_config/`)
These JSON files contain:
- Pre-recorded attack scenarios
- Metadata (feature names, value types, timestamp formats)
- Time-series data for demonstration purposes
- Instance-specific values for each time point

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
- Reads data from static JSON files (e.g., `static_data_config/demo_5_values.json`, `static_data_config/demo_9_values.json`, `static_data_config/demo_10_DDOS_values.json`, `static_data_config/demo_10_apiEXP_values.json`)
- Useful for demos and testing without live Elasticsearch
- Iterates through pre-defined data rows on each polling cycle
- Automatically sets `LIVE_DATA=false` when enabled
- **This is the default mode for all demos**

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
| `--demo` | `5`, `9`, `10` | Specifies the demo number |
| `--demo_mode` | `api_exposure`, `ddos` | Sets the attack scenario type (Demo 10 only) |
| `--static_mode` | `true`, `false` | Enables/disables static data mode (default: `true`) |
| `--live_data` | `true`, `false` | Enables/disables live real-time querying (default: `false`) |
| `--deployment_domain` | `CNIT`, `UMU`, `UPC` | Sets testbed-specific endpoints |
| `--polling_interval` | Integer (seconds) | Sets the query interval in seconds |
| `--ES_DATA_START_TIME` | ISO 8601 timestamp | Start time for time-range mode |
| `--ES_DATA_END_TIME` | ISO 8601 timestamp | End time for time-range mode |

**Note**: All demos default to `STATIC_MODE=true` and `LIVE_DATA=false` for safe demonstration purposes. To use live data or time-range mode, explicitly set these parameters.

### Demo Mode Details

#### Demo 5
When `--demo 5` is specified:
- `CONFIG_FILE_PATH=./data_queries_config/config_demo_5.json`
- `STATIC_DATA_FILE_PATH=static_data_config/demo_5_values.json`
- **Default modes**:
  - `STATIC_MODE=true`
  - `LIVE_DATA=false`
- Default time range:
  - `ES_DATA_START_TIME=2025-07-14T00:36:00.000Z`
  - `ES_DATA_END_TIME=2025-07-14T01:04:00.000Z`
- Uses `multidomain_dns_data` index
- Features 2 instances representing multi-domain testbeds:
  - `node1:CNIT` - CNIT Testbed node
  - `node1:UPC` - UPC Testbed node
- Feature: DNS (DNS traffic monitoring)
- 15 data points with 120-second intervals
- Demonstrates synchronized multi-domain attack scenario

#### Demo 9
When `--demo 9` is specified:
- `CONFIG_FILE_PATH=./data_queries_config/config_demo_9.json`
- `STATIC_DATA_FILE_PATH=static_data_config/demo_9_values.json`
- **Default modes**:
  - `STATIC_MODE=true`
  - `LIVE_DATA=false`
- Default time range:
  - `ES_DATA_START_TIME=2024-11-11T13:03:30.146Z`
  - `ES_DATA_END_TIME=2025-07-24T13:04:23.133Z`
- Uses `pcap_data` index
- Features 9 instances with NEF (Network Exposure Function) feature

#### Demo 10
When `--demo 10` is specified:
- **Default modes**:
  - `STATIC_MODE=true`
  - `LIVE_DATA=false`
  - `DEMO_MODE=api_exposure` (if not specified)
  - `DEPLOYMENT_DOMAIN=CNIT` (if not specified)
- **api_exposure**: 
  - `CONFIG_FILE_PATH=./data_queries_config/config_demo10.json`
  - `STATIC_DATA_FILE_PATH=static_data_config/demo_10_apiEXP_values.json`
  - Default time range (when `STATIC_MODE=false` and `LIVE_DATA=false`):
    - `ES_DATA_START_TIME=2025-12-16T13:31:03.000Z`
    - `ES_DATA_END_TIME=2025-12-16T13:39:03.000Z`
- **ddos**:
  - `CONFIG_FILE_PATH=./data_queries_config/config_demo10.json`
  - `STATIC_DATA_FILE_PATH=static_data_config/demo_10_DDOS_values.json`
  - Default time range (when `STATIC_MODE=false` and `LIVE_DATA=false`):
    - `ES_DATA_START_TIME=2025-12-11T16:00:55.000Z`
    - `ES_DATA_END_TIME=2025-12-11T16:07:55.000Z`
- Uses `holo_demo_data_api` index

### Deployment Domain Details

| Domain | Elasticsearch URL | DEME URL |
|--------|-------------------|----------|
| **CNIT** | `http://192.168.130.48:9200` | `http://192.168.130.110:8090/estimate` |
| **UMU** | `http://10.208.11.69:9200` | `http://10.208.11.69:8090/estimate` |
| **UPC** | `http://10.19.2.15:9200` | `http://10.19.2.16:8090/estimate` |

---

## Usage Examples

### Demo 5 Examples

#### Example 1: Demo 5 - Static Mode Multi-Domain Demo
Run Demo 5 using pre-recorded multi-domain DNS attack data:
```bash
./deploy.sh --demo 5 --static_mode true
```

#### Example 2: Demo 5 - Time Range Replay (CNIT + UPC)
Replay Demo 5 showing synchronized attack across CNIT and UPC testbeds:
```bash
./deploy.sh --demo 5 --deployment_domain CNIT --static_mode false --live_data false
```
This automatically uses the default time range covering the multi-domain attack scenario.

#### Example 3: Demo 5 - Custom Polling for Multi-Domain Monitoring
Run Demo 5 with faster polling to capture rapid changes:
```bash
./deploy.sh --demo 5 --static_mode true --polling_interval 60
```

#### Example 4: Demo 5 - Live Multi-Domain Monitoring
Monitor live DNS traffic across multiple domains:
```bash
./deploy.sh --demo 5 --deployment_domain CNIT --live_data true
```

#### Example 5: Demo 5 - Full Configuration
Complete multi-domain deployment with all parameters:
```bash
./deploy.sh \
  --demo 5 \
  --deployment_domain CNIT \
  --static_mode false \
  --live_data false \
  --polling_interval 120 \
  --ES_DATA_START_TIME "2025-07-14T00:36:00.000Z" \
  --ES_DATA_END_TIME "2025-07-14T01:04:00.000Z"
```

### Demo 9 Examples

#### Example 1: Demo 9 - Static Mode with Default Settings
Run Demo 9 using pre-recorded static data:
```bash
./deploy.sh --demo 9 --static_mode true
```

#### Example 2: Demo 9 - Time Range Replay on CNIT Testbed
Replay Demo 9 historical data with automatic time range:
```bash
./deploy.sh --demo 9 --deployment_domain CNIT --static_mode false --live_data false
```
This automatically sets:
- `ES_DATA_START_TIME=2024-11-11T13:03:30.146Z`
- `ES_DATA_END_TIME=2025-07-24T13:04:23.133Z`

#### Example 3: Demo 9 - Custom Time Range on UMU Testbed
Replay Demo 9 with a custom time range:
```bash
./deploy.sh --demo 9 --deployment_domain UMU --static_mode false --live_data false \
  --ES_DATA_START_TIME "2024-11-11T13:03:30.146Z" \
  --ES_DATA_END_TIME "2024-11-11T13:30:00.000Z" \
  --polling_interval 120
```

#### Example 4: Demo 9 - Live Data Mode
Monitor live data using Demo 9 configuration:
```bash
./deploy.sh --demo 9 --deployment_domain CNIT --live_data true
```

### Demo 10 Examples

#### Example 1: Demo 10 - Live Data Mode (API Exposure) on CNIT
Deploy in real-time monitoring mode for API exposure detection:
```bash
./deploy.sh --demo 10 --demo_mode api_exposure --deployment_domain CNIT --live_data true
```

#### Example 2: Demo 10 - Live Data Mode (DDoS) on UMU
Monitor for DDoS attacks in real-time:
```bash
./deploy.sh --demo 10 --demo_mode ddos --deployment_domain UMU --live_data true
```

#### Example 3: Demo 10 - Time Range Replay with Defaults
Replay Demo 10 API exposure attack using automatic time range:
```bash
./deploy.sh --demo 10 --demo_mode api_exposure --deployment_domain UPC
```
This automatically uses Demo 10's default time range for api_exposure.

#### Example 4: Demo 10 - Static Data Demo (DDoS)
Run a demo using pre-recorded static data:
```bash
./deploy.sh --demo 10 --demo_mode ddos --static_mode true
```

#### Example 5: Demo 10 - Custom Time Range Replay
Replay historical data from a custom time range:
```bash
./deploy.sh --demo 10 --demo_mode api_exposure --deployment_domain UPC \
  --ES_DATA_START_TIME "2025-12-16T12:28:32.176Z" \
  --ES_DATA_END_TIME "2025-12-16T12:40:40.072Z"
```

### General Configuration Examples

#### Example 1: Quick Switch to Live Mode
Quickly switch the current deployment to live data mode:
```bash
./deploy.sh --live_data true
```

#### Example 2: Change Deployment Domain Only
Switch to a different testbed without changing other settings:
```bash
./deploy.sh --deployment_domain CNIT
```

#### Example 3: Adjust Polling Interval
Change the query frequency to 60 seconds:
```bash
./deploy.sh --polling_interval 60
```

#### Example 4: Full Configuration (Demo 10)
Complete deployment with all parameters specified:
```bash
./deploy.sh \
  --demo 10 \
  --demo_mode api_exposure \
  --deployment_domain CNIT \
  --static_mode false \
  --live_data false \
  --polling_interval 120 \
  --ES_DATA_START_TIME "2025-12-16T12:28:32.176Z" \
  --ES_DATA_END_TIME "2025-12-16T12:40:40.072Z"
```

---

## Environment Variables

The following environment variables are configured in the `.env` file:

### Elasticsearch Configuration
- `ES_USERNAME`: Elasticsearch username (default: `elastic`)
- `ES_PASSWORD`: Elasticsearch password
- `ES_INDEX`: Index to query (default from .env, but overridden by config file when `STATIC_MODE=false`)
  - Demo 9 uses: `pcap_data`
  - Demo 10 uses: `holo_demo_data_api`
- `ES_ANALYTICS_INDEX`: Analytics index name (default: `analytics_index`)
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
Example for live data mode (Demo 10):
```properties
STATIC_MODE=false
LIVE_DATA=true
CONFIG_FILE_PATH=./data_queries_config/config_demo10.json
STATIC_DATA_FILE_PATH=static_data_config/demo_10_DDOS_values.json
POLLING_INTERVAL=120
ES_DATA_START_TIME=
ES_DATA_END_TIME=
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
```

Example for static demo mode (Demo 5 - Multi-Domain):
```properties
STATIC_MODE=true
LIVE_DATA=false
CONFIG_FILE_PATH=./data_queries_config/config_demo_5.json
STATIC_DATA_FILE_PATH=static_data_config/demo_5_values.json
POLLING_INTERVAL=120
ES_DATA_START_TIME=2025-07-14T00:36:00.000Z
ES_DATA_END_TIME=2025-07-14T01:04:00.000Z
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
```

Example for static demo mode (Demo 9):
```properties
STATIC_MODE=true
LIVE_DATA=false
CONFIG_FILE_PATH=./data_queries_config/config_demo_9.json
STATIC_DATA_FILE_PATH=static_data_config/demo_9_values.json
POLLING_INTERVAL=120
ES_DATA_START_TIME=2024-11-11T13:03:30.146Z
ES_DATA_END_TIME=2025-07-24T13:04:23.133Z
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

Example output for Demo 5 (Static mode):
```
Configuration updated. Current settings:
-------------------------------------------
CONFIG_FILE_PATH=./data_queries_config/config_demo_5.json
STATIC_DATA_FILE_PATH=static_data_config/demo_5_values.json
STATIC_MODE=true
LIVE_DATA=false
POLLING_INTERVAL=120
ES_DATA_START_TIME=2025-07-14T00:36:00.000Z
ES_DATA_END_TIME=2025-07-14T01:04:00.000Z
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
-------------------------------------------
```

Example output for Demo 10 (Live mode):
```
Configuration updated. Current settings:
-------------------------------------------
CONFIG_FILE_PATH=./data_queries_config/config_demo10.json
STATIC_DATA_FILE_PATH=static_data_config/demo_10_DDOS_values.json
STATIC_MODE=false
LIVE_DATA=true
POLLING_INTERVAL=120
ES_DATA_START_TIME=
ES_DATA_END_TIME=
ES_URL=http://192.168.130.48:9200
AFTER_PRE_PROCESSING_URL=http://192.168.130.110:8090/estimate
-------------------------------------------
```

Example output for Demo 9 (Static mode):
```
Configuration updated. Current settings:
-------------------------------------------
CONFIG_FILE_PATH=./data_queries_config/config_demo_9.json
STATIC_DATA_FILE_PATH=static_data_config/demo_9_values.json
STATIC_MODE=true
LIVE_DATA=false
POLLING_INTERVAL=120
ES_DATA_START_TIME=2024-11-11T13:03:30.146Z
ES_DATA_END_TIME=2025-07-24T13:04:23.133Z
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
- Verify the static data file exists:
  - Demo 5: `app/static_data_config/demo_5_values.json`
  - Demo 9: `app/static_data_config/demo_9_values.json`
  - Demo 10 API Exposure: `app/static_data_config/demo_10_apiEXP_values.json`
  - Demo 10 DDoS: `app/static_data_config/demo_10_DDOS_values.json`
- Verify the config file exists:
  - Demo 5: `app/data_queries_config/config_demo_5.json`
  - Demo 9: `app/data_queries_config/config_demo_9.json`
  - Demo 10: `app/data_queries_config/config_demo10.json`

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

- All demos default to `STATIC_MODE=true` and `LIVE_DATA=false` to ensure safe demonstration without requiring live Elasticsearch connectivity
- The deployment script uses `sed` to update `.env` file, which works on Linux/macOS/Git Bash
- On Windows without Git Bash, consider using WSL or manually editing `.env`
- All timestamps should be in ISO 8601 format with 'Z' suffix or timezone offset
- The `POLLING_INTERVAL` determines how frequently queries are executed (in seconds)
- When `LIVE_DATA=true`, time range parameters are automatically cleared to avoid conflicts
- When `STATIC_MODE=true`, it automatically sets `LIVE_DATA=false` to prevent conflicts
- `STATIC_MODE` and `LIVE_DATA` are mutually exclusive - only one can be `true` at a time
- Each demo has a specific Elasticsearch index defined in its config file:
  - Demo 5: Uses `multidomain_dns_data` index
  - Demo 9: Uses `pcap_data` index
  - Demo 10: Uses `holo_demo_data_api` index
- The index specified in the config file takes precedence over the `ES_INDEX` in `.env` when `STATIC_MODE=false`

---

## Support

For issues or questions, please refer to the HORSE project documentation or contact the development team.
