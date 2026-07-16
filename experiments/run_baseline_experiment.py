#!/usr/bin/env python3
"""
Baseline Connectivity Experiment.

Demonstrates the functionality of the ExperimentRuntime. It overrides the 
`execute_experiment` method strictly to prove end-to-end traffic routing 
operates natively within the orchestrated lifecycle. Does not implement 
packet inference, probing, or attack logic.
"""

import os
import sys
from pathlib import Path

from experiments.experiment_runtime import BaseExperiment
from framework.traffic.traffic_generator import TrafficGenerator


class BaselineConnectivityExperiment(BaseExperiment):
    """
    Dummy experiment that tests Layer 7 Application connectivity through 
    the orchestrated VPN baseline to prove lifecycle robustness.
    """
    
    def execute_experiment(self) -> None:
        """Executes the specific experimental logic."""
        app_ip = self._get_app_server_ip()
        self.logger.info(f"Originating traffic from client targeting {app_ip}:8000 (HTTP)")
        
        # Utilize the existing TrafficGenerator
        generator = TrafficGenerator(self.ns_manager, source_ns="client")
        
        success, out = generator.generate_http(app_ip, 8000)
        
        self.logger.info(f"Transaction Success: {success}")
        self.logger.info(f"Application Output:  {out.split('|')[-1] if '|' in out else out}")
        
        # Record findings to be serialized in generate_report()
        self.results_data["experiment_success"] = success and "HTTP_PAYLOAD_OK" in out
        self.results_data["target_ip"] = app_ip


def main() -> None:
    if is_admin() != 0:
        print("FATAL: Root privileges required for kernel state orchestration.")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent.parent
    
    experiment = BaselineConnectivityExperiment(
        experiment_name="baseline_connectivity_demo",
        base_dir=base_dir
    )
    
    experiment.run()


if __name__ == "__main__":
    main()