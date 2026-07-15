"""
Cleanup & Resource Management Module.

Acts as a centralized registry for all infrastructure components provisioned 
during an experiment. Guarantees that namespaces, processes, and capture 
engines are safely torn down, even if fatal exceptions occur.
"""

import logging
from typing import List, Any
from lab.topology.topology_builder import TopologyBuilder
from lab.start_servers import ServiceOrchestrator
from framework.observation.capture import CapturePipeline

logger = logging.getLogger("ExperimentRuntime")


class ResourceCleanupManager:
    """Tracks and tears down registered system resources in reverse order."""

    def __init__(self) -> None:
        self._topology_builders: List[TopologyBuilder] = []
        self._orchestrators: List[ServiceOrchestrator] = []
        self._capture_pipelines: List[CapturePipeline] = []

    def register_topology(self, builder: TopologyBuilder) -> None:
        """Registers a TopologyBuilder for teardown."""
        self._topology_builders.append(builder)

    def register_orchestrator(self, orchestrator: ServiceOrchestrator) -> None:
        """Registers a ServiceOrchestrator for teardown."""
        self._orchestrators.append(orchestrator)

    def register_capture(self, pipeline: CapturePipeline) -> None:
        """Registers a CapturePipeline for safe shutdown."""
        self._capture_pipelines.append(pipeline)

    def execute_cleanup(self) -> None:
        """
        Executes teardown on all registered resources. 
        Catches and logs individual teardown failures to ensure the pipeline 
        attempts to clean up everything before exiting.
        """
        logger.info("\n=== Executing Automated Resource Cleanup ===")

        for pipeline in self._capture_pipelines:
            try:
                logger.info("Stopping observation capture pipeline...")
                pipeline.stop()
            except Exception as e:
                logger.error(f"Failed to stop capture pipeline: {e}")

        for orchestrator in self._orchestrators:
            try:
                logger.info("Terminating background application services...")
                orchestrator.stop_all()
            except Exception as e:
                logger.error(f"Failed to stop background services: {e}")

        for builder in self._topology_builders:
            try:
                logger.info("Destroying network namespaces and interfaces...")
                builder.teardown()
            except Exception as e:
                logger.error(f"Failed to teardown topology: {e}")
                
        logger.info("[+] Cleanup sequence completed.")