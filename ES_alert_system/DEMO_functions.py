import subprocess
import os
import time
import json
import pyshark
import requests
import logging

from scapy.all import rdpcap
from scapy.layers.inet import IP, UDP
from scapy.layers.dns import DNS
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEME_url = 'http://your-api-endpoint'
NKUA_DTE_url = 'http://91.138.223.127'

def capture_network(interface, output_path, capture_duration=60):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    command = ["sudo", "tshark", "-a", f"duration:{capture_duration}", "-i", interface, "-w", output_path]
    
    try:
        print(f"Starting network capture on interface {interface}...")
        subprocess.run(command, check=True)
        print(f"Capture completed. Output saved to: {output_path}")
        adjust_file_permissions(output_path)  # Adjust permissions after capture
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during capture: {e}")

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
        logging.info("PFCP message counts: %s", message_counts)
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
        forward_response = requests.post(fastapi_url, json=response.json(), headers=headers)
        if forward_response.status_code == 200:
            logging.info("Successfully forwarded data to FastAPI.")
        else:
            logging.info(f"Failed to forward data to FastAPI: {forward_response.text}")
    else:
        logging.info(f"Failed to send data to BentoML: {response.text}")

def process_capture(pcap_file):
    count_pfcp_messages(pcap_file)

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


# The function print_ip_packet_counts reads a pcap file, counts specific 
# IP packets within two-minute windows, and prints the counts. 
# It specifically looks for packets with the 
# UDP destination or source port of 123 (typically associated with NTP) and 
# containing the NTPPrivate layer with a mode of 7 (indicating NTP MONLIST packets).
def print_ip_packet_counts(pcap_file):
    # Read the pcap file
    packets = rdpcap(pcap_file)
    
    # Initialize variables
    ip_packets_count = 0
    start_time = None

    for packet in packets:
        # Check if the packet has an IP layer
        if packet.haslayer(IP) and packet.haslayer(UDP):
            if packet[UDP].dport == 123 or packet[UDP].sport == 123:
                if packet.haslayer(NTPPrivate) and packet[NTPPrivate].mode == 7:

                    # Extract the packet's timestamp
                    packet_time = (datetime.fromtimestamp(float(packet.time)))

                    # Initialize start_time if it's the first packet
                    if start_time is None:
                        start_time = packet_time

                    # Check if the packet is within the current two-minute window
                    if packet_time < start_time + timedelta(minutes=2):
                        ip_packets_count += 1
                    else:
                        # Print the count for the past two minutes
                        print(f"From {start_time} to {start_time + timedelta(minutes=2)}: {ip_packets_count} IP packets")
                        
                        # Reset the count and start_time for the next two-minute window
                        start_time = packet_time
                        ip_packets_count = 1  # Start counting the current packet

    # Print the count for the last window if there were any packets
    if start_time is not None:
        print(f"From {start_time} to {start_time + timedelta(minutes=2)}: {ip_packets_count} NTP MONLIST packets")

def print_dns_packet_bytes(pcap_file):
    # Read the pcap file
    packets = rdpcap(pcap_file)
    
    # Initialize variables
    dns_packets_bytes = 0
    start_time = None

    for packet in packets:
        # Check if the packet has both IP and UDP layers
        if packet.haslayer(IP) and packet.haslayer(UDP):
            # Check if the packet has a DNS layer
            if packet.haslayer(DNS):
                # Extract the packet's timestamp
                packet_time = datetime.fromtimestamp(float(packet.time))
                
                # Initialize start_time if it's the first packet
                if start_time is None:
                    start_time = packet_time
                
                # Check if the packet is within the current two-minute window
                if packet_time < start_time + timedelta(minutes=2):
                    dns_packets_bytes += len(packet)  # Accumulate the size of the DNS packet
                else:
                    # Print the total bytes for the past two minutes
                    print(f"From {start_time} to {start_time + timedelta(minutes=2)}: {dns_packets_bytes} bytes of DNS packets")
                    
                    # Reset the count and start_time for the next two-minute window
                    start_time = packet_time
                    dns_packets_bytes = len(packet)  # Start counting the current packet's size

    # Print the total bytes for the last window if there were any packets
    if start_time is not None:
        print(f"From {start_time} to {start_time + timedelta(minutes=2)}: {dns_packets_bytes} bytes of DNS packets")


def main():
    interface = "br-2110472eacd1"
    output_directory = "./pcap_files"
    output_filename = "demo-cnit_testbed-a.pcap"
    pcap_file = os.path.join(output_directory, output_filename)
    
    while True:
        # Uncomment the following line if you want to perform network capture in each loop
        # capture_network(interface, pcap_file, capture_duration=60)
        process_capture(pcap_file)
        print("Sleeping for 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main()
