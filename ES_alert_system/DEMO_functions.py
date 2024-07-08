import subprocess
import os
import time
import json
import time
import threading
import pyshark
import requests

DEME_url = 'http://your-api-endpoint'
NKUA_DTE_url = 'http://91.138.223.127'



def adjust_file_permissions(file_path):
    try:
        os.chmod(file_path, 0o644)  # Readable and writable by owner, readable by others
        logging.info(f"Permissions adjusted for file: {file_path}")
    except Exception as e:
        logging.info(f"Failed to adjust permissions for file {file_path}: {e}")

def capture_network(interface, output_path, capture_duration=60):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    command = ["sudo", "tshark", "-a", f"duration:{capture_duration}", "-i", interface, "-w", output_path]
    
    try:
        logging.info(f"Starting network capture on interface {interface}...")
        subprocess.run(command, check=True)
        logging.info(f"Capture completed. Output saved to: {output_path}")
        adjust_file_permissions(output_path)  # Adjust permissions after capture
    except subprocess.CalledProcessError as e:
        logging.info(f"An error occurred during capture: {e}")

def count_pfcp_messages(pcap_file):
    message_counts = {
        "PFCPHeartbeatRequest_counter": 0,
        "PFCPHeartbeatResponse_counter": 0,
        "PFCPSessionEstablishmentRequest_counter": 0,
        "PFCPSessionEstablishmentResponse_counter": 0,
        "PFCPSessionModificationRequest_counter": 0,
        "PFCPSessionModificationResponse_counter": 0
    }

    try:
        cap = pyshark.FileCapture(pcap_file, display_filter="udp.port == 8805")
        for packet in cap:
            if hasattr(packet, 'pfcp'):
                message_type = int(packet.pfcp.msg_type)
                if message_type == 1:
                    message_counts["PFCPHeartbeatRequest_counter"] += 1
                elif message_type == 2:
                    message_counts["PFCPHeartbeatResponse_counter"] += 1
                elif message_type == 50:
                    message_counts["PFCPSessionEstablishmentRequest_counter"] += 1
                elif message_type == 51:
                    message_counts["PFCPSessionEstablishmentResponse_counter"] += 1
                elif message_type == 52:
                    message_counts["PFCPSessionModificationRequest_counter"] += 1
                elif message_type == 53:
                    message_counts["PFCPSessionModificationResponse_counter"] += 1
        logging.info("PFCP message counts:", message_counts)
        send_to_bentoml(message_counts)  # Send the counts to BentoML
    except Exception as e:
        logging.info(f"Error processing pcap file: {e}")
    finally:
        if 'cap' in locals():
            cap.close()

def send_to_bentoml(message_counts):
    url = NKUA_DTE_url + ':5000/predict'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=message_counts, headers=headers)
    fastapi_url= NKUA_DTE_url + ':9898/receive-data/'
    
    if response.status_code == 200:
        logging.info("Successfully sent data to BentoML.")
        logging.info(response.text)
        forward_response= requests.post(fastapi_url, json=response.json(), headers=headers)
        if forward_response.status_code == 200:
            logging.info("Successfully forwarded data to FastAPI.")
        else:
            logging.info(f"Failed to forward data to FastAPI: {forward_response.text}")
    else:
        logging.info(f"Failed to send data to BentoML: {response.text}")

def process_capture_in_background(pcap_file):
    processing_thread = threading.Thread(target=count_pfcp_messages, args=(pcap_file,))
    processing_thread.start()



def read_pcap_for_DEME(pcap_file, instance_name="Test_Instance"):
    message_counts = count_pfcp_messages(pcap_file)
    if not message_counts:
        logging.error("Failed to extract message counts from pcap file.")
        return None

    timestamp = int(time.time())
    features = [{"feature": k, "value": v} for k, v in message_counts.items()]
    response_body = [
        {
            "timestamp": str(timestamp),
            "instances": [
                {
                    "instance": instance_name,
                    "features": features
                }
            ]
        }
    ]
    
    return response_body

def send_data_to_DEME(response_body):
    url = DEME_url + '/estimate'
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=response_body, headers=headers)
        if response.status_code == 200:
            logging.info("Successfully sent estimate request.")
            logging.info(f"Response: {response.json()}")
        else:
            logging.error(f"Failed to send estimate request: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"An error occurred while sending estimate request: {e}")




def main():
    interface = "br-2110472eacd1"
    output_directory = "/home/userdev/horse/bento-wireshark"
    output_filename = "capture.pcap"
    pcap_file = os.path.join(output_directory, output_filename)
    
    while True:
        capture_network(interface, pcap_file, capture_duration=60)
        process_capture_in_background(pcap_file)
        print("Sleeping for 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main()
