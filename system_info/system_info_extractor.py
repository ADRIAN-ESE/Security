import platform
import socket
import uuid
import requests
import json
import os
import subprocess
from datetime import datetime
from getmac import get_mac_address


class SystemInfoExtractor:
    """
    Extracts comprehensive system information and geolocation data.
    Educational tool for understanding digital footprinting and system reconnaissance.

    WARNING: This tool extracts sensitive system information. Use only on systems
    you own or have explicit written permission to analyze. Misuse may violate
    privacy laws and computer fraud statutes.
    """

    def __init__(self):
        """Initialize data structure to store extracted information."""
        self.data = {
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'network': {},
            'geolocation': {}
        }

    def get_system_info(self):
        """
        Extract operating system and hardware information.

        Returns:
            dict: System information including OS, architecture, and hardware details
        """
        print("🔍 Collecting system information...")

        self.data['system'] = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'platform_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname(),
            'python_version': platform.python_version(),
            'node_name': platform.node()
        }
        return self.data['system']

    def get_network_info(self):
        """
        Extract network configuration and MAC addresses.

        Returns:
            dict: Network details including IP addresses and MAC address
        """
        print("🌐 Collecting network information...")

        try:
            # Get MAC address using getmac library (cross-platform)
            mac = get_mac_address()

            # Get local IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            # Get public IP address
            public_ip = self._get_public_ip()

            # Get default gateway
            gateway = self._get_default_gateway()

            self.data['network'] = {
                'hostname': hostname,
                'local_ip': local_ip,
                'public_ip': public_ip,
                'mac_address': mac,
                'default_gateway': gateway
            }
        except Exception as e:
            self.data['network'] = {'error': str(e)}

        return self.data['network']

    def _get_public_ip(self):
        """
        Fetch public IP address using external API.

        Returns:
            str: Public IP address or error message
        """
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json().get('ip')
        except:
            return 'Unable to retrieve'

    def _get_default_gateway(self):
        """
        Attempt to get default gateway using system commands.

        Returns:
            str: Default gateway IP or error message
        """
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Default Gateway' in line and ':' in line:
                        gateway = line.split(':')[-1].strip()
                        if gateway:
                            return gateway
            else:
                # Linux/Mac
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'default' in line:
                        parts = line.split()
                        if 'via' in parts:
                            return parts[parts.index('via') + 1]
            return 'Unknown'
        except Exception as e:
            return f'Error: {str(e)}'

    def get_geolocation(self):
        """
        Fetch geolocation data based on public IP using ip-api.com.
        Free tier: 45 requests per minute from same IP.

        Returns:
            dict: Geolocation data including country, city, ISP, and coordinates
        """
        print("📍 Fetching geolocation data...")

        try:
            public_ip = self.data['network'].get('public_ip')
            if not public_ip or public_ip == 'Unable to retrieve':
                self.data['geolocation'] = {'error': 'No public IP available'}
                return self.data['geolocation']

            # Using ip-api.com (free, no API key required for non-commercial use)
            # Fields documentation: https://ip-api.com/docs/
            response = requests.get(
                f'http://ip-api.com/json/{public_ip}?fields=status,message,continent,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting',
                timeout=5
            )

            if response.status_code == 200:
                geo_data = response.json()
                if geo_data.get('status') == 'success':
                    self.data['geolocation'] = {
                        'country': geo_data.get('country'),
                        'country_code': geo_data.get('countryCode'),
                        'region': geo_data.get('regionName'),
                        'city': geo_data.get('city'),
                        'zip': geo_data.get('zip'),
                        'latitude': geo_data.get('lat'),
                        'longitude': geo_data.get('lon'),
                        'timezone': geo_data.get('timezone'),
                        'isp': geo_data.get('isp'),
                        'organization': geo_data.get('org'),
                        'autonomous_system': geo_data.get('as'),
                        'is_mobile': geo_data.get('mobile', False),
                        'is_proxy': geo_data.get('proxy', False),
                        'is_hosting': geo_data.get('hosting', False)
                    }
                else:
                    self.data['geolocation'] = {'error': geo_data.get('message', 'Unknown error')}
            else:
                self.data['geolocation'] = {'error': f'HTTP {response.status_code}'}

        except Exception as e:
            self.data['geolocation'] = {'error': str(e)}

        return self.data['geolocation']

    def generate_report(self, format_type='console'):
        """
        Generate formatted report in specified format.

        Args:
            format_type (str): 'console', 'json', or 'html'

        Returns:
            str: Formatted report
        """
        if format_type == 'console':
            return self._console_report()
        elif format_type == 'json':
            return json.dumps(self.data, indent=2)
        elif format_type == 'html':
            return self._html_report()
        else:
            raise ValueError("Invalid format_type. Choose 'console', 'json', or 'html'")

    def _console_report(self):
        """
        Generate console-friendly formatted report with emojis and alignment.

        Returns:
            str: Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("🔐 SYSTEM INFORMATION & GEOLOCATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {self.data['timestamp']}")
        report.append("")

        # System Section
        report.append("🖥️  SYSTEM INFORMATION")
        report.append("-" * 40)
        for key, value in self.data['system'].items():
            report.append(f"  {key.replace('_', ' ').title():<20}: {value}")
        report.append("")

        # Network Section
        report.append("🌐 NETWORK INFORMATION")
        report.append("-" * 40)
        for key, value in self.data['network'].items():
            if key == 'mac_address':
                value = str(value).upper() if value else 'N/A'
            report.append(f"  {key.replace('_', ' ').title():<20}: {value}")
        report.append("")

        # Geolocation Section
        report.append("📍 GEOLOCATION INFORMATION")
        report.append("-" * 40)
        if 'error' in self.data['geolocation']:
            report.append(f"  Error: {self.data['geolocation']['error']}")
        else:
            for key, value in self.data['geolocation'].items():
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                report.append(f"  {key.replace('_', ' ').title():<20}: {value}")
        report.append("")
        report.append("=" * 60)
        report.append("⚠️  Security Note: This information could be used for")
        report.append("    system fingerprinting and targeted attacks.")
        report.append("=" * 60)

        return '\n'.join(report)

    def _html_report(self):
        """
        Generate professional HTML report with CSS styling.

        Returns:
            str: HTML document
        """
        # Build system table rows
        system_rows = "".join([
            f"<tr><th>{k.replace('_', ' ').title()}</th><td>{v}</td></tr>"
            for k, v in self.data['system'].items()
        ])

        # Build network table rows
        network_rows = "".join([
            f"<tr><th>{k.replace('_', ' ').title()}</th><td>{str(v).upper() if k == 'mac_address' and v else v}</td></tr>"
            for k, v in self.data['network'].items()
        ])

        # Build geolocation table rows or error message
        if 'error' in self.data['geolocation']:
            geo_rows = f'<tr><td colspan="2" style="color: red;">Error: {self.data["geolocation"]["error"]}</td></tr>'
        else:
            geo_rows = "".join([
                f"<tr><th>{k.replace('_', ' ').title()}</th><td>{('Yes' if v else 'No') if isinstance(v, bool) else v}</td></tr>"
                for k, v in self.data['geolocation'].items()
            ])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Information Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 4px solid #3498db; 
            padding-bottom: 15px;
            margin-bottom: 10px;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 35px; 
            border-left: 5px solid #3498db; 
            padding-left: 15px;
            font-size: 1.4em;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            padding: 14px; 
            text-align: left; 
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{ 
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white; 
            width: 40%;
            font-weight: 600;
        }}
        tr:hover {{ 
            background-color: #f5f9ff;
            transition: background-color 0.3s;
        }}
        .warning {{ 
            background: #fff3cd; 
            border-left: 6px solid #ffc107; 
            padding: 20px; 
            margin-top: 40px; 
            border-radius: 8px;
            color: #856404;
        }}
        .timestamp {{ 
            color: #7f8c8d; 
            font-style: italic;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 System Information & Geolocation Report</h1>
        <p class="timestamp">Generated: {self.data['timestamp']}</p>

        <h2>🖥️ System Information</h2>
        <table>
            {system_rows}
        </table>

        <h2>🌐 Network Information</h2>
        <table>
            {network_rows}
        </table>

        <h2>📍 Geolocation Information</h2>
        <table>
            {geo_rows}
        </table>

        <div class="warning">
            <strong>⚠️ Security Notice:</strong> This information reveals sensitive details about your system 
            that could be used for targeted attacks, system fingerprinting, or social engineering. 
            Always protect this data and be cautious about sharing it publicly.
        </div>
    </div>
</body>
</html>"""
        return html

    def save_report(self, filename='system_report', formats=None):
        """
        Save report to files in specified formats.

        Args:
            filename (str): Base filename without extension
            formats (list): List of formats to save ('json', 'html')

        Returns:
            list: List of saved filenames
        """
        if formats is None:
            formats = ['json', 'html']

        saved_files = []

        if 'json' in formats:
            json_file = f"{filename}.json"
            with open(json_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            saved_files.append(json_file)
            print(f"✅ JSON report saved: {json_file}")

        if 'html' in formats:
            html_file = f"{filename}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(self._html_report())
            saved_files.append(html_file)
            print(f"✅ HTML report saved: {html_file}")

        return saved_files

    def run_full_analysis(self):
        """
        Execute complete system analysis workflow.

        Returns:
            dict: Complete extracted data
        """
        print("\n" + "=" * 60)
        print("🔍 STARTING SYSTEM ANALYSIS")
        print("=" * 60 + "\n")

        self.get_system_info()
        self.get_network_info()
        self.get_geolocation()

        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 60 + "\n")

        return self.data


def main():
    """Main execution function with error handling."""
    try:
        # Create extractor instance
        extractor = SystemInfoExtractor()

        # Run full analysis
        data = extractor.run_full_analysis()

        # Display console report
        print(extractor.generate_report('console'))

        # Save reports
        print("\n💾 Saving reports...")
        files = extractor.save_report('my_system_info', ['json', 'html'])

        print(f"\n🎉 Done! Check your files: {', '.join(files)}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


if __name__ == "__main__":
    main()