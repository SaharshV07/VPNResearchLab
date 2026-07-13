import os
import subprocess
import sys

def build_repository_structure():
    """Generates the comprehensive VPNResearchLab nested directory structure."""
    
    # List of all deep subdirectories requested
    nested_directories = [
        # Documentation
        "docs/paper", "docs/paper/figures", "docs/architecture", 
        "docs/roadmap", "docs/presentations", "docs/experiment_logs",
        
        # Configurations
        "configs/wireguard", "configs/openvpn", "configs/sysctl", 
        "configs/iptables", "configs/routing", "configs/namespaces",
        
        # Core Framework Packages
        "framework/observation", "framework/networking", "framework/packet", 
        "framework/traffic", "framework/metrics", "framework/storage", 
        "framework/visualization", "framework/orchestration", "framework/utils",
        
        # Virtualized Lab Environment
        "lab/topology", "lab/namespaces", "lab/vpn", 
        "lab/routers", "lab/servers", "lab/startup", "lab/teardown",
        # Chronological Research Experiments
        "experiments/experiment00_environment", "experiments/experiment01_capture",
        "experiments/experiment02_metadata", "experiments/experiment03_vpn_validation",
        "experiments/experiment04_client_validation", "experiments/experiment05_server_validation",
        "experiments/experiment06_nat_analysis", "experiments/experiment07_parameter_variation",
        "experiments/experiment08_final_demo",
        
        # Flat Data, Analysis, & Test Roots
        "datasets", "results", "notebooks", "reports", "tests"
    ]
    
    print("📁 Constructing nested repository architecture...")
    for path in nested_directories:
        os.makedirs(path, exist_ok=True)
        
        # Automatically make framework folders valid Python submodules
        if path.startswith("framework"):
            init_file = os.path.join(path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    pass

    # Ensure a root init exists for the main package block
    with open(os.path.join("framework", "__init__.py"), "w") as f:
        pass
        
    print("✅ All directories and sub-packages successfully initialized.")

def populate_boilerplate_files():
    """Creates initial structural, meta, and standard configuration file layouts."""
    print("📝 Populating standard repository root files...")
    
    files_to_create = {
        "LICENSE": "MIT License\n\nCopyright (c) 2026 VPNResearchLab Team",
        "CONTRIBUTING.md": "# Contributing to VPNResearchLab\n\nThank you for helping reproduce academic network observations.",
        "pyproject.toml": '[build-system]\nrequires = ["setuptools", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "VPNResearchLab"\nversion = "0.1.0"\ndescription = "An academic network research framework for encrypted tunnels and traffic analysis."',
        "requirements.txt": "scapy==2.5.0\npandas==2.2.2\nnotebook==7.2.1\nmatplotlib==3.9.0",
        ".gitignore": ".venv/\n__pycache__/\n*.pyc\ndatasets/\nresults/*.db\nresults/*.sqlite\n.vscode/\n.idea/\n.DS_Store",
        "docs/paper/notes.md": "# Research Paper Reading Notes",
        "docs/paper/attack_flow.md": "# Blind In-On-Path Attacks Visual Flowchart Documentation"
    }
    
    for filepath, context in files_to_create.items():
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(context)
                
    print("✅ Boilerplate configuration files added.")

def run_environment_setup():
    """Creates a local Python virtual environment to run simulations safely."""
    print("🐍 Provisioning safe virtual environment isolation (.venv)...")
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Environment successfully generated.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed environment deployment: {e}")

def main() -> None:
    print("==================================================")
    print("      🚀 VPNResearchLab Advanced Deployer         ")
    print("==================================================")
    build_repository_structure()
    populate_boilerplate_files()
    run_environment_setup()
    print("\n🎉 Architecture Complete! Initialize development via terminal:")
    print("   👉 Windows:    .venv\\Scripts\\activate")
    print("   👉 Mac/Linux:  source .venv/bin/activate")

if __name__ == "__main__":
    main()
