# System Architecture

The VPNResearchLab is built on a highly modular architecture ensuring strict separation of concerns between environment provisioning, traffic generation, and data observation.

## 1. Observation Engine (`framework/`)
The core instrument of the laboratory. It passively monitors defined network interfaces, strips payloads, and structures metadata into high-performance `dataclass` models. 
*   **Capture Subsystem:** Handles asynchronous I/O streams using Scapy and libpcap.
*   **Metadata Extractor:** Translates raw bytes into structured schema.
*   **Metrics Aggregator:** Computes stateful flow statistics, such as Inter-Arrival Time (IAT).

## 2. Networking Layer (`lab/` and `configs/`)
Responsible for establishing the deterministic environment required for experiments. 
*   Uses Linux Network Namespaces to simulate isolated nodes (Client, Gateway, Router, VPN Server, Target).
*   Manages precise `sysctl` kernel variable tuning (e.g., `rp_filter`).
*   Orchestrates the cryptographic tunnel processes (OpenVPN/WireGuard).

## 3. Experiments (`experiments/`)
The execution layer. Each experiment is an isolated script that imports the topology, triggers the background traffic generation, initializes the Observation Engine, and executes specific test conditions (e.g., sweeping port arrays).

## 4. Results Pipeline (`results/` and `notebooks/`)
The analytical layer. It ingests the JSONL/SQLite outputs from the Observation Engine, calculates empirical probabilities, and generates static visualizations (histograms, timelines, scatter plots) to prove or disprove hypotheses.