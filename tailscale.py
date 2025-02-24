from typing import Any
import subprocess
import json
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
import argparse

# Initialize FastMCP server
mcp = FastMCP("tailscale")

# Constants
TAILSCALE_PATH = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"

@dataclass
class TailscaleDevice:
    ip: str
    name: str
    dns_name: str
    user: str
    os: str
    status: str
    last_seen: str
    rx_bytes: int
    tx_bytes: int

def parse_tailscale_status(json_data: dict) -> list[TailscaleDevice]:
    """Parse the JSON output of tailscale status into structured data."""
    devices = []

    # Add self device
    self_device = json_data["Self"]
    devices.append(TailscaleDevice(
        ip=self_device["TailscaleIPs"][0],
        name=self_device["HostName"],
        dns_name=self_device["DNSName"],
        user=json_data["User"][str(self_device["UserID"])]["LoginName"],
        os=self_device["OS"],
        status="online" if self_device["Online"] else "offline",
        last_seen="current device",
        rx_bytes=self_device["RxBytes"],
        tx_bytes=self_device["TxBytes"]
    ))

    # Add peer devices
    for peer in json_data["Peer"].values():
        devices.append(TailscaleDevice(
            ip=peer["TailscaleIPs"][0],
            name=peer["HostName"],
            dns_name=peer["DNSName"],
            user=json_data["User"][str(peer["UserID"])]["LoginName"],
            os=peer["OS"],
            status="online" if peer["Online"] else "offline",
            last_seen=peer["LastSeen"],
            rx_bytes=peer["RxBytes"],
            tx_bytes=peer["TxBytes"]
        ))

    return devices

def run_tailscale_command(args: list[str]) -> dict:
    """Run a Tailscale command and return its JSON output."""
    try:
        result = subprocess.run(
            [TAILSCALE_PATH] + args + ["--json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error running Tailscale command: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing Tailscale JSON output: {str(e)}")

@mcp.tool()
async def get_tailscale_status() -> str:
    """Get the status of all Tailscale devices in your network."""
    try:
        output = run_tailscale_command(["status"])
        devices = parse_tailscale_status(output)

        if not devices:
            return "No Tailscale devices found."

        # Format the response in a readable way
        response_parts = ["Your Tailscale Network Devices:"]
        for device in devices:
            traffic = ""
            if device.rx_bytes > 0 or device.tx_bytes > 0:
                traffic = f"\nTraffic: rx {device.rx_bytes:,} bytes, tx {device.tx_bytes:,} bytes"

            status_info = f"""
Device: {device.name}
DNS Name: {device.dns_name}
IP: {device.ip}
User: {device.user}
OS: {device.os}
Status: {device.status}
Last seen: {device.last_seen}{traffic}
"""
            response_parts.append(status_info)

        return "\n---\n".join(response_parts)
    except Exception as e:
        return f"Error getting Tailscale status: {str(e)}"

@mcp.tool()
async def get_device_info(device_name: str) -> str:
    """Get detailed information about a specific Tailscale device.

    Args:
        device_name: The name of the Tailscale device to query
    """
    try:
        output = run_tailscale_command(["status"])
        devices = parse_tailscale_status(output)

        for device in devices:
            if device.name.lower() == device_name.lower():
                traffic = ""
                if device.rx_bytes > 0 or device.tx_bytes > 0:
                    traffic = f"\nTraffic:\n  Received: {device.rx_bytes:,} bytes\n  Transmitted: {device.tx_bytes:,} bytes"

                return f"""
Detailed information for {device.name}:
DNS Name: {device.dns_name}
IP Address: {device.ip}
User: {device.user}
Operating System: {device.os}
Current Status: {device.status}
Last Seen: {device.last_seen}{traffic}
"""

        return f"No device found with name: {device_name}"
    except Exception as e:
        return f"Error getting device info: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Tailscale MCP server')
    parser.add_argument('--transport', choices=['stdio', 'http'], default='stdio',
                      help='Transport type (stdio or http)')
    parser.add_argument('--port', type=int, default=3000,
                      help='Port for HTTP server (only used with --transport http)')
    args = parser.parse_args()

    if args.transport == 'http':
        mcp.settings.port = args.port
        mcp.run(transport='sse')
    else:
        # Run with stdio transport
        mcp.run(transport='stdio')