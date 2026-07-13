# Implementation Roadmap

## Milestone 1: Observation Framework Foundation
*   Define core data models and strict typing constraints.
*   Implement stateless PCAP parsing and metadata extraction.
*   Implement SQLite and JSONLines storage sinks.

## Milestone 2: Asynchronous Capture Engine
*   Build the asynchronous packet sniffing loop.
*   Verify microsecond-level timestamp accuracy across multiple interfaces.
*   Integrate stateful flow tracking and statistical metric calculation.

## Milestone 3: Network Laboratory Provisioning
*   Script Linux Network Namespace creation and teardown.
*   Verify virtual Ethernet (veth) routing and isolation.
*   Deploy baseline VPN tunnel configuration between Client and Server nodes.

## Milestone 4: Traffic Generation and Simulation
*   Create automated background traffic profiles (HTTP, DNS).
*   Validate `conntrack` state creation on the VPN server node.

## Milestone 5: Experiment Execution
*   Develop Phase 1 Client-Side Weak Host routing verification script.
*   Develop Server-Side NAT Port multiplexing verification script.
*   Execute, measure, and log all findings to the Results Pipeline.