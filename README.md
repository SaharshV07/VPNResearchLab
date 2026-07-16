# VPNResearchLab

## Project Overview
VPNResearchLab is an academic network research framework designed to study the behaviors of encrypted tunnels, routing policies, and Network Address Translation (NAT). It provides a highly controlled, modular environment to systematically measure, observe, and document network state changes resulting from varying kernel configurations.

## Research Goal
To independently reproduce the network state observations and traffic analysis experiments detailed in "Blind In/On-Path Attacks and Applications to VPNs". The framework abstracts away experimental boilerplate, allowing researchers to focus strictly on packet analysis, metadata extraction, and statistical measurement of tunneled traffic.

## Architecture
The framework is divided into five distinct domains:
*   **Observation Engine:** Asynchronous traffic capture, parsing, and metric aggregation.
*   **Networking Layer:** Virtualized network topology, routing definitions, and VPN orchestration.
*   **Experiments:** Modular execution scripts defining distinct test conditions.
*   **Results Pipeline:** Statistical analysis, persistent storage, and visualization of captured metadata.
*   **Lab:** Infrastructure provisioning for localized multi-node testing environments.

## Directory Structure
*   `configs/`: Template files for network and tunnel configurations.
*   `datasets/`: Raw packet captures (PCAP/PCAPNG).
*   `docs/`: System architecture and research roadmaps.
*   `experiments/`: Executable research scenarios.
*   `framework/`: The core Python package (Observation Engine).
*   `lab/`: Topologies and infrastructure definitions.
*   `notebooks/`: Jupyter environments for exploratory data analysis.
*   `reports/`: Exported research findings.
*   `results/`: Parsed datasets and SQLite databases.
*   `tests/`: Unit and integration testing suites.

## Installation
```bash
git clone [https://github.com/username/VPNResearchLab.git](https://github.com/username/VPNResearchLab.git)
cd VPNResearchLab
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


## Repository Verification

Before executing any experiments or provisioning the lab, it is critical to verify the repository health. A cross-platform verification utility is provided to ensure all dependencies, imports, and system requirements are met.

### Usage
Execute the health check from the root of the repository:
```bash
python healthcheck.py