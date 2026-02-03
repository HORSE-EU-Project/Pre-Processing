#!/bin/bash

# Default values
DEMO=""
DEMO_MODE=""
STATIC_MODE=""
LIVE_DATA=""
ES_DATA_START_TIME=""
ES_DATA_END_TIME=""
DEPLOYMENT_DOMAIN=""
POLLING_INTERVAL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --demo)
            DEMO="$2"
            shift 2
            ;;
        --demo_mode)
            DEMO_MODE="$2"
            shift 2
            ;;
        --static_mode)
            STATIC_MODE="$2"
            shift 2
            ;;
        --live_data)
            LIVE_DATA="$2"
            shift 2
            ;;
        --ES_DATA_START_TIME)
            ES_DATA_START_TIME="$2"
            shift 2
            ;;
        --ES_DATA_END_TIME)
            ES_DATA_END_TIME="$2"
            shift 2
            ;;
        --deployment_domain)
            DEPLOYMENT_DOMAIN="$2"
            shift 2
            ;;
        --polling_interval)
            POLLING_INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--demo <value>] [--demo_mode <api_exposure|ddos>] [--static_mode <true|false>] [--live_data <true|false>] [--deployment_domain <CNIT|UPC|UMU>] [--polling_interval <seconds>] [--ES_DATA_START_TIME <time>] [--ES_DATA_END_TIME <time>]"
            exit 1
            ;;
    esac
done

# Function to update .env file
update_env_file() {
    local key=$1
    local value=$2
    
    if grep -q "^${key}=" .env; then
        # Key exists, update it
        sed -i "s|^${key}=.*|${key}=${value}|" .env
    else
        # Key doesn't exist, append it
        echo "${key}=${value}" >> .env
    fi
}

echo "Starting deployment configuration..."

# Set Demo 10 defaults if demo=10 and parameters are not explicitly provided
if [ "$DEMO" = "10" ]; then
    # Set default values only if not already specified by user
    if [ -z "$DEMO_MODE" ]; then
        DEMO_MODE="api_exposure"
        echo "Using Demo 10 default demo_mode: api_exposure"
    fi
    
    if [ -z "$DEPLOYMENT_DOMAIN" ]; then
        DEPLOYMENT_DOMAIN="CNIT"
        echo "Using Demo 10 default deployment_domain: CNIT"
    fi
    
    if [ -z "$STATIC_MODE" ]; then
        STATIC_MODE="false"
        echo "Using Demo 10 default static_mode: false"
    fi
    
    if [ -z "$LIVE_DATA" ]; then
        LIVE_DATA="false"
        echo "Using Demo 10 default live_data: false"
    fi
    
    if [ -z "$ES_DATA_START_TIME" ]; then
        ES_DATA_START_TIME="2025-12-16T12:28:32.176Z"
        echo "Using Demo 10 default ES_DATA_START_TIME: 2025-12-16T12:28:32.176Z"
    fi
    
    if [ -z "$ES_DATA_END_TIME" ]; then
        ES_DATA_END_TIME="2025-12-16T12:40:40.072Z"
        echo "Using Demo 10 default ES_DATA_END_TIME: 2025-12-16T12:40:40.072Z"
    fi
fi

# Handle deployment domain configuration
if [ -n "$DEPLOYMENT_DOMAIN" ]; then
    echo "Configuring for deployment domain: $DEPLOYMENT_DOMAIN"
    
    case "$DEPLOYMENT_DOMAIN" in
        CNIT)
            echo "Setting endpoints for CNIT Testbed"
            update_env_file "ES_URL" "http://192.168.130.48:9200"
            update_env_file "AFTER_PRE_PROCESSING_URL" "http://192.168.130.110:8090/estimate"
            ;;
        UMU)
            echo "Setting endpoints for UMU Testbed"
            update_env_file "ES_URL" "http://127.0.0.1:9200"
            update_env_file "AFTER_PRE_PROCESSING_URL" "http://127.0.0.1:8090/estimate"
            ;;
        UPC)
            echo "Setting endpoints for UPC Testbed"
            update_env_file "ES_URL" "http://10.19.2.15:9200"
            update_env_file "AFTER_PRE_PROCESSING_URL" "http://10.19.2.16:8090/estimate"
            ;;
        *)
            echo "Warning: Unknown deployment_domain '$DEPLOYMENT_DOMAIN'. Valid options are: CNIT, UMU, UPC"
            ;;
    esac
fi

# Handle demo configuration
if [ "$DEMO" = "10" ]; then
    echo "Configuring for Demo 10..."
    
    if [ "$DEMO_MODE" = "api_exposure" ]; then
        echo "Demo mode: API Exposure"
        update_env_file "CONFIG_FILE_PATH" "./config_demo10.json"
        update_env_file "STATIC_DATA_FILE_PATH" "demo_10_apiEXP_values.json"
    elif [ "$DEMO_MODE" = "ddos" ]; then
        echo "Demo mode: DDoS"
        update_env_file "CONFIG_FILE_PATH" "./config_demo10.json"
        update_env_file "STATIC_DATA_FILE_PATH" "demo_10_DDOS_values.json"
    elif [ -n "$DEMO_MODE" ]; then
        echo "Warning: Unknown demo_mode '$DEMO_MODE'. Valid options are: api_exposure, ddos"
    fi
fi

# Update static mode if provided
if [ -n "$STATIC_MODE" ]; then
    echo "Setting static mode: $STATIC_MODE"
    update_env_file "STATIC_MODE" "$STATIC_MODE"
    
    # If STATIC_MODE is true, automatically set LIVE_DATA to false
    if [ "$STATIC_MODE" = "true" ]; then
        echo "Static mode is enabled - automatically setting LIVE_DATA to false"
        LIVE_DATA="false"
        update_env_file "LIVE_DATA" "false"
    fi
fi

# Update live data mode if provided
if [ -n "$LIVE_DATA" ]; then
    # Check if user is trying to set LIVE_DATA=true while STATIC_MODE=true
    if [ "$LIVE_DATA" = "true" ] && [ "$STATIC_MODE" = "true" ]; then
        echo "WARNING: Cannot enable LIVE_DATA while STATIC_MODE is true!"
        echo "STATIC_MODE and LIVE_DATA are mutually exclusive."
        echo "Keeping LIVE_DATA as false."
        LIVE_DATA="false"
    fi
    
    echo "Setting live data mode: $LIVE_DATA"
    update_env_file "LIVE_DATA" "$LIVE_DATA"
    
    # If LIVE_DATA=true, clear the time range to enable real-time querying
    if [ "$LIVE_DATA" = "true" ]; then
        echo "Live data mode enabled - clearing time range parameters for real-time querying"
        update_env_file "ES_DATA_START_TIME" ""
        update_env_file "ES_DATA_END_TIME" ""
    fi
fi

# Update ES_DATA_START_TIME if provided (only if not in live data mode)
if [ -n "$ES_DATA_START_TIME" ] && [ "$LIVE_DATA" != "true" ]; then
    echo "Setting ES_DATA_START_TIME: $ES_DATA_START_TIME"
    update_env_file "ES_DATA_START_TIME" "$ES_DATA_START_TIME"
fi

# Update ES_DATA_END_TIME if provided (only if not in live data mode)
if [ -n "$ES_DATA_END_TIME" ] && [ "$LIVE_DATA" != "true" ]; then
    echo "Setting ES_DATA_END_TIME: $ES_DATA_END_TIME"
    update_env_file "ES_DATA_END_TIME" "$ES_DATA_END_TIME"
fi

# Update POLLING_INTERVAL if provided
if [ -n "$POLLING_INTERVAL" ]; then
    echo "Setting POLLING_INTERVAL: $POLLING_INTERVAL seconds"
    update_env_file "POLLING_INTERVAL" "$POLLING_INTERVAL"
fi

echo ""
echo "Configuration updated. Current settings:"
echo "-------------------------------------------"
grep -E "CONFIG_FILE_PATH|STATIC_DATA_FILE_PATH|STATIC_MODE|LIVE_DATA|POLLING_INTERVAL|ES_DATA_START_TIME|ES_DATA_END_TIME|ES_URL|AFTER_PRE_PROCESSING_URL" .env
echo "-------------------------------------------"
echo ""

# Deploy with docker-compose
echo "Stopping existing containers..."
docker-compose down

echo "Building and starting containers..."
docker-compose up --build -d

echo ""
echo "Deployment complete!"
echo "To view logs, run: docker-compose logs -f"
