from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Threat:
    name: str = ""
    description: str = ""

@dataclass
class Vulnerability:
    name: str = ""
    description: str = ""

@dataclass
class ExploitPath:
    name: str = ""
    description: str = ""

@dataclass
class RiskPrioritization:
    threat: str = ""
    likelihood: str = ""
    impact: str = ""
    risk_rating: str = ""

@dataclass
class Mitigation:
    name: str = ""
    description: str = ""

@dataclass
class Documentation:
    threat_model_documentation: str = ""
    update_frequency: str = ""

@dataclass
class AttackSurface:
    user_interfaces: List[str] = field(default_factory=list)
    apis: List[str] = field(default_factory=list)
    data_storage: List[str] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    third_party_services: List[str] = field(default_factory=list)
    infrastructure: List[str] = field(default_factory=list)

@dataclass
class BusinessContext:
    business_criticality: str = ""
    data_classification: str = ""
    regulatory_requirements: List[str] = field(default_factory=list)
    business_impact: str = ""

@dataclass
class ThreatModel:
    application_name: str = ""
    version: str = ""
    business_context: BusinessContext = field(default_factory=BusinessContext)
    components: List[str] = field(default_factory=list)
    entrypoints: List[str] = field(default_factory=list)
    attack_surface: AttackSurface = field(default_factory=AttackSurface)
    threats: List[Threat] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    exploit_paths: List[ExploitPath] = field(default_factory=list)
    risk_prioritization: List[RiskPrioritization] = field(default_factory=list)
    mitigations: List[Mitigation] = field(default_factory=list)
    documentation: Documentation = field(default_factory=Documentation)

# Example Usage
if __name__ == "__main__":
    # Create an empty threat model
    threat_model = ThreatModel()

    # Populate with example data
    threat_model.application_name = "Example Web Application"
    threat_model.version = "1.0"
    threat_model.components = ["frontend", "backend", "database"]
    threat_model.entrypoints = ["web", "api"]

    threat_model.threats.append(Threat(name="Spoofing", description="An attacker impersonates a user or system."))
    threat_model.vulnerabilities.append(Vulnerability(name="Input Validation", description="Lack of proper input validation."))

    threat_model.risk_prioritization.append(
        RiskPrioritization(threat="Spoofing", likelihood="Medium", impact="High", risk_rating="High")
    )

    threat_model.mitigations.append(
        Mitigation(name="Input Validation and Sanitization", description="Implement strict input validation.")
    )

    # Print the threat model
    print(threat_model)