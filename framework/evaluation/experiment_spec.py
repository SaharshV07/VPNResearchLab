"""
Experiment Specification Module.

Serves as the master schema for defining a reproducible networking experiment.
Binds the environment requirements and artifact manifest into a single, validable unit.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

from framework.evaluation.environment_requirements import EnvironmentRequirements
from framework.evaluation.artifact_manifest import ArtifactManifest


@dataclass(frozen=True, slots=True)
class ExperimentSpecification:
    """
    The master blueprint defining WHAT an experiment is and WHAT it requires.
    
    Attributes:
        experiment_id: Unique string identifier (e.g., 'exp_01_vip_inference').
        version: Specification version for tracking updates.
        objective: Human-readable description of the experimental goal.
        required_config_files: Paths to the YAML configs that must be loaded.
        environment: The EnvironmentRequirements defining the required topology state.
        expected_manifest: The ArtifactManifest defining the expected outputs.
        validation_criteria: Key-value assertions to evaluate experiment success.
    """
    experiment_id: str
    version: str
    objective: str
    required_config_files: List[Path]
    environment: EnvironmentRequirements
    expected_manifest: ArtifactManifest
    validation_criteria: Dict[str, Any] = field(default_factory=dict)

    def validate_metadata(self) -> None:
        """
        Performs a sanity check on the specification itself to ensure no 
        fields are left blank or improperly configured.
        
        Raises:
            ValueError: If metadata is incomplete or malformed.
        """
        if not self.experiment_id or not self.experiment_id.strip():
            raise ValueError("ExperimentSpecification requires a valid 'experiment_id'.")
            
        if not self.version or not self.version.strip():
            raise ValueError("ExperimentSpecification requires a valid 'version'.")
            
        if not self.objective or not self.objective.strip():
            raise ValueError("ExperimentSpecification requires a clear 'objective'.")
            
        if not self.required_config_files:
            raise ValueError("ExperimentSpecification must declare at least one required config file.")