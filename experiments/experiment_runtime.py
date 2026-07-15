"""
Experiment Runtime Module.

Provides the abstract BaseExperiment class, defining the strict lifecycle 
required to provision, verify, execute, and destroy a VPN research experiment.
"""

import time
import abc
import json
from pathlib import Path
from typing import Dict, Any

from lab.config import LabConfiguration
from lab.vpn.config import VPNConfiguration
from lab.topology.namespace_manager import NamespaceManager, LabConfig as NsConfig
from lab.topology.topology_builder import TopologyBuilder
from lab.topology.routing_manager import RoutingManager
from lab.topology.network_builder import NetworkBuilder
from lab.vpn.vpn_manager import VPNManager
from lab.vpn.validator import VPNValidator
from lab.start_servers import ServiceOrchestrator
from framework.traffic.traffic_generator import TrafficGenerator

from experiments.runtime_logger import setup_runtime_logger
from experiments.cleanup import ResourceCleanupManager


class BaseExperiment(abc.ABC):
    """
    Abstract base class for all research experiments.
    Enforces the strict lifecycle sequence and manages underlying dependencies.
    """

    def __init__(self, experiment_name: str, base_dir: Path) -> None:
        self.experiment_name = experiment_name
        self.base_dir = base_dir
        self.log_dir = base_dir / "reports" / "logs"
        self.results_dir = base_dir / "results" / experiment_name
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_runtime_logger(self.experiment_name, self.log_dir)
        self.cleanup_manager = ResourceCleanupManager()
        
        # Infrastructure state
        self.lab_config: LabConfiguration
        self.vpn_config: VPNConfiguration
        self.ns_manager: NamespaceManager
        self.builder: TopologyBuilder
        self.vpn_manager: VPNManager
        self.orchestrator: ServiceOrchestrator
        self.results_data: Dict[str, Any] = {"experiment": experiment_name}

    def _get_app_server_ip(self) -> str:
        """Helper to extract the target IP dynamically from configuration."""
        for ns in self.lab_config.namespaces:
            if ns.name == "app_server":
                return ns.interfaces[0].ip.split('/')[0]
        return ""

    def initialize(self) -> None:
        self.logger.info("=== Phase 1: Initialization ===")
        lab_yaml = self.base_dir / "configs" / "topology.yaml"
        vpn_yaml = self.base_dir / "configs" / "vpn" / "wireguard.yaml"
        
        self.lab_config = LabConfiguration.load(lab_yaml)
        self.vpn_config = VPNConfiguration.load(vpn_yaml)
        
        ns_names = [n.name for n in self.lab_config.namespaces]
        self.ns_manager = NamespaceManager(NsConfig(namespaces=ns_names))
        
        self.builder = TopologyBuilder(self.lab_config)
        self.cleanup_manager.register_topology(self.builder)
        
        self.vpn_manager = VPNManager(
            self.vpn_config, 
            self.ns_manager
        )
        
        self.orchestrator = ServiceOrchestrator(target_ns="app_server")
        self.cleanup_manager.register_orchestrator(self.orchestrator)
        self.logger.info("[+] Configurations loaded and managers instantiated.")

    def setup_lab(self) -> None:
        self.logger.info("\n=== Phase 2: Setup Laboratory ===")
        self.builder.teardown()  # Ensure pristine state
        self.builder.build()

    def deploy_vpn(self) -> None:
        self.logger.info("\n=== Phase 3: Deploy Encrypted VPN Tunnel ===")
        self.vpn_manager.deploy()

    def start_background_services(self) -> None:
        self.logger.info("\n=== Phase 4: Start Background Services ===")
        self.orchestrator.start_all()

    def wait_until_ready(self) -> None:
        self.logger.info("\n=== Phase 5: Awaiting Environment Stability ===")
        time.sleep(2.0)  # Allow sockets to bind and interfaces to transition to UP state
        self.logger.info("[+] Environment is stable.")

    def verify_environment(self) -> None:
        self.logger.info("\n=== Phase 6: Baseline Verification ===")
        app_ip = self._get_app_server_ip()
        validator = VPNValidator(self.vpn_config, self.ns_manager)
        res = validator.validate(app_ip)
        
        if not all([res.namespaces, res.interfaces, res.handshake, res.routing, res.nat, res.connectivity]):
            self.logger.error("[!] Environment failed baseline verification. Aborting experiment.")
            raise RuntimeError("Baseline VPN environment is invalid.")
        self.logger.info("[+] Environment mathematically verified.")

    @abc.abstractmethod
    def execute_experiment(self) -> None:
        """To be implemented by the specific research experiment."""
        pass

    def collect_results(self) -> None:
        self.logger.info("\n=== Phase 8: Result Collection ===")
        # Allows subclasses to serialize specific findings
        pass

    def generate_report(self) -> None:
        self.logger.info("\n=== Phase 9: Report Generation ===")
        report_path = self.results_dir / "experiment_summary.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results_data, f, indent=4)
        self.logger.info(f"[+] Report saved to {report_path}")

    def cleanup(self) -> None:
        self.cleanup_manager.execute_cleanup()

    def run(self) -> None:
        """
        Master execution wrapper. Guarantees the strict lifecycle ordering 
        and ensures cleanup always runs via try-finally.
        """
        try:
            self.logger.info(f"--- Starting Experiment: {self.experiment_name} ---")
            self.initialize()
            self.setup_lab()
            self.deploy_vpn()
            self.start_background_services()
            self.wait_until_ready()
            self.verify_environment()
            
            self.logger.info("\n=== Phase 7: Execute Experiment ===")
            self.execute_experiment()
            
            self.collect_results()
            self.generate_report()
            
        except Exception as e:
            self.logger.error(f"\n[FATAL] Experiment failed unexpectedly: {e}")
        finally:
            self.cleanup()
            self.logger.info(f"--- Experiment Completed: {self.experiment_name} ---")