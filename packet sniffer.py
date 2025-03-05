from scapy.all import *

def sniff_packets(interface="eth0"):
    """Sniffs packets on the specified network interface.

    Args:
        interface (str): The network interface to sniff packets from.

    Returns:
        None
    """

    try:
        # Start sniffing packets
        sniff(iface=interface, prn=lambda x: print(x.summary()))
    except Exception as e:
        print(f"Error sniffing packets: {e}")

if __name__ == "__main__":
    interface = input("Enter the network interface to sniff (e.g., eth0, wlan0): ")
    sniff_packets(interface)