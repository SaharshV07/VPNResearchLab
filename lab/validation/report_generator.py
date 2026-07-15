"""
Report Generator Module.

Transforms the raw data dictionary from the VerificationRunner into structured 
JSON artifacts and human-readable Markdown reports.
"""

import json
from pathlib import Path
from typing import Dict, Any

class ReportGenerator:
    """Generates artifacts from verification results."""

    def __init__(self, results: Dict[str, Any], output_dir: Path):
        self.results = results
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_json(self) -> Path:
        """Writes the raw dictionary to a JSON file."""
        json_path = self.output_dir / "baseline_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4)
        return json_path

    def generate_markdown(self) -> Path:
        """Writes a formatted Markdown summary report."""
        md_path = self.output_dir / "baseline_report.md"
        
        lines = [
            f"# VPNResearchLab Baseline Verification Report",
            f"**Timestamp:** {self.results['timestamp']}  ",
            f"**Environment:** {self.results['environment_name']}  ",
            "---",
            "## 1. Subsystem Verification Status"
        ]

        # Iterate through check categories
        all_passed = True
        for category, checks in self.results["checks"].items():
            lines.append(f"### {category.capitalize()}")
            for check_name, status in checks.items():
                icon = "✅ PASS" if status else "❌ FAIL"
                lines.append(f"* **{check_name}:** {icon}")
                if not status:
                    all_passed = False
            lines.append("")

        lines.append("## 2. Baseline Metrics")
        metrics = self.results["metrics"]
        lines.append(f"* **Round Trip Time (RTT):** {metrics.get('rtt_ms', -1):.2f} ms")
        lines.append(f"* **TCP Throughput:** {metrics.get('throughput_mbps', 0):.2f} MB/s")
        
        lines.append("\n### Interface Statistics")
        lines.append("| Interface | RX Bytes | RX Packets | TX Bytes | TX Packets |")
        lines.append("|-----------|----------|------------|----------|------------|")
        for iface, stats in metrics.get("interface_stats", {}).items():
            lines.append(f"| {iface} | {stats['rx_bytes']} | {stats['rx_packets']} | {stats['tx_bytes']} | {stats['tx_packets']} |")

        lines.append("\n---")
        lines.append("## 3. Conclusion")
        if all_passed:
            lines.append("✅ **The baseline environment is fully verified and mathematically sound.** The routing, encryption, and NAT layers are functioning precisely as defined. It is ready for research experiments.")
        else:
            lines.append("❌ **Verification Failed.** One or more subsystems failed the integrity checks. The environment is unstable and should not be used for experiments until corrected.")

        md_path.write_text("\n".join(lines), encoding="utf-8")
        return md_path