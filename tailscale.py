import subprocess
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("tailscale")

# Constants
TAILSCALE_PATH = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"

@dataclass
class TailscaleDevice:
    ip: str
    name: str
    user: str
    os: str
    status: str

def parse_tailscale_status(output: str) -> list[TailscaleDevice]:
    """Parse the output of tailscale status into structured data."""
    devices = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        # Split but keep the status part (which might contain spaces) together
        parts = line.split(None, 4)
        if len(parts) >= 4:
            ip, name, user, os = parts[:4]
            raw_status = parts[4] if len(parts) > 4 else "-"

            # Convert "-" to "online"
            status = "online" if raw_status == "-" else raw_status

            devices.append(TailscaleDevice(
                ip=ip,
                name=name,
                user=user,
                os=os,
                status=status
            ))
    return devices

def run_tailscale_command(args: list[str]) -> str:
    """Run a Tailscale command and return its output."""
    try:
        result = subprocess.run(
            [TAILSCALE_PATH] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running Tailscale command: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_tailscale_status() -> str:
    """Get the status of all Tailscale devices in your network."""
    output = run_tailscale_command(["status"])
    devices = parse_tailscale_status(output)

    if not devices:
        return "No Tailscale devices found or error reading status."

    # Format the response in a readable way
    response_parts = ["Your Tailscale Network Devices:"]
    for device in devices:
        status_info = f"""
Device: {device.name}
IP: {device.ip}
User: {device.user}
OS: {device.os}
Status: {device.status}
"""
        response_parts.append(status_info)

    return "\n---\n".join(response_parts)

@mcp.tool()
async def get_device_info(device_name: str) -> str:
    """Get detailed information about a specific Tailscale device.

    Args:
        device_name: The name of the Tailscale device to query
    """
    output = run_tailscale_command(["status"])
    devices = parse_tailscale_status(output)

    for device in devices:
        if device.name.lower() == device_name.lower():
            return f"""
Detailed information for {device.name}:
IP Address: {device.ip}
User: {device.user}
Operating System: {device.os}
Current Status: {device.status}
"""

    return f"No device found with name: {device_name}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
