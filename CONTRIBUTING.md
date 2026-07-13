# Contributing to VPNResearchLab

We welcome contributions from the academic and security research communities. To maintain the integrity and reproducibility of the research framework, please adhere to the following guidelines.

## Development Standards
1.  **Code Formatting:** All Python code must be formatted using `black` and linted with `ruff`.
2.  **Type Hinting:** Strict type hinting is enforced. Run `mypy` before submitting any pull requests.
3.  **Testing:** All new features within the `framework/` directory must be accompanied by comprehensive `pytest` coverage.
4.  **No Exploit Tooling:** This repository is strictly for measurement, observation, and simulation. Submissions adding offensive automation will be rejected.

## Pull Request Process
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/observation-upgrade`).
3.  Commit your changes following conventional commit messages.
4.  Push to the branch (`git push origin feature/observation-upgrade`).
5.  Open a Pull Request detailing the purpose, changes, and required testing steps.