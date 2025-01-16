from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, JSON, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from typing import Dict, List
from enum import Enum as PyEnum
from datetime import datetime

Base = declarative_base()

# Association tables for many-to-many relationships
finding_cve = Table(
    'finding_cve',
    Base.metadata,
    Column('finding_id', Integer, ForeignKey('findings.id')),
    Column('cve_id', Integer, ForeignKey('cves.id'))
)

class Severity(PyEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Finding(Base):
    __tablename__ = 'findings'

    id = Column(Integer, primary_key=True)
    vulnerability_type = Column(String, nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    affected_package = Column(String)
    code_snippet = Column(String)
    file_path = Column(String)
    line_number = Column(Integer)
    description = Column(String, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    source_tool = Column(String, nullable=False)
    hash = Column(String, unique=True)  # Hash of the finding for deduplication
    
    # Analysis results
    false_positive_likelihood = Column(String)
    exploitability_score = Column(Integer)
    impact_score = Column(Integer)
    
    # Relationships
    report_id = Column(Integer, ForeignKey('security_reports.id'))
    report = relationship("SecurityReport", back_populates="findings")
    cves = relationship("CVE", secondary=finding_cve, back_populates="findings")
    similar_findings = relationship("SimilarFinding", back_populates="finding")
    remediation_steps = relationship("RemediationStep", back_populates="finding")
    contexts = relationship("FindingContext", back_populates="finding")

class SecurityReport(Base):
    __tablename__ = 'security_reports'

    id = Column(Integer, primary_key=True)
    project_name = Column(String, nullable=False)
    scan_date = Column(DateTime, default=func.now())
    git_commit = Column(String)
    summary = Column(String)
    
    # Analysis metadata
    total_files_scanned = Column(Integer)
    total_findings = Column(Integer)
    tools_used = Column(JSON)  # List of tools used in the scan
    
    # Relationships
    findings = relationship("Finding", back_populates="report")

class CVE(Base):
    __tablename__ = 'cves'

    id = Column(Integer, primary_key=True)
    cve_id = Column(String, unique=True, nullable=False)
    description = Column(String)
    cvss_score = Column(Float)
    published_date = Column(DateTime)
    reference_urls = Column(JSON)  # List of reference URLs
    
    # Relationships
    findings = relationship("Finding", secondary=finding_cve, back_populates="cves")

class SimilarFinding(Base):
    __tablename__ = 'similar_findings'

    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey('findings.id'))
    similar_code = Column(String)
    similarity_score = Column(Float)
    file_path = Column(String)
    
    # Relationships
    finding = relationship("Finding", back_populates="similar_findings")

class RemediationStep(Base):
    __tablename__ = 'remediation_steps'

    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey('findings.id'))
    step_number = Column(Integer)
    description = Column(String)
    code_example = Column(String)
    
    # Relationships
    finding = relationship("Finding", back_populates="remediation_steps")

class FindingContext(Base):
    __tablename__ = 'finding_contexts'

    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey('findings.id'))
    context_type = Column(String)  # e.g., "code", "dependency", "configuration"
    context_data = Column(JSON)
    
    # Relationships
    finding = relationship("Finding", back_populates="contexts")

# Helper methods for the Finding model
def create_finding_from_tool_result(tool_name: str, result: Dict) -> Finding:
    """Create a Finding instance from a tool result"""
    return Finding(
        vulnerability_type=result.get('type'),
        severity=Severity(result.get('severity', 'MEDIUM').upper()),
        affected_package=result.get('package'),
        code_snippet=result.get('code'),
        file_path=result.get('file'),
        line_number=result.get('line'),
        description=result.get('description'),
        source_tool=tool_name,
        hash=generate_finding_hash(result)  # Implement hash generation for deduplication
    )

def generate_finding_hash(result: Dict) -> str:
    """Generate a unique hash for a finding to help with deduplication"""
    # Implement hash generation logic based on relevant fields
    pass 