from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import uuid

db = SQLAlchemy()

class RuleAction(str, Enum):
    """FlowSpec rule actions"""
    DISCARD = "discard"
    ACCEPT = "accept"
    RATE_LIMIT = "rate-limit"

class RuleStatus(str, Enum):
    """Rule deployment status"""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    ERROR = "error"

class FlowSpecRule(db.Model):
    """FlowSpec rule model"""
    __tablename__ = 'flowspec_rules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Match criteria
    source_ip = db.Column(db.String(43))  # IPv4/IPv6 CIDR
    destination_ip = db.Column(db.String(43))
    protocol = db.Column(db.String(10))  # tcp, udp, icmp, etc.
    source_port = db.Column(db.String(255))  # comma-separated or range
    destination_port = db.Column(db.String(255))
    dscp = db.Column(db.Integer)  # Differentiated Services Code Point
    fragment_offset = db.Column(db.Integer)
    
    # Action
    action = db.Column(db.Enum(RuleAction), default=RuleAction.DISCARD, nullable=False)
    rate_limit_value = db.Column(db.Integer)  # in kbps, if action is rate-limit
    
    # Status and lifecycle
    status = db.Column(db.Enum(RuleStatus), default=RuleStatus.DRAFT, nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)
    withdrawn_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)  # TTL expiration
    
    # Metadata
    created_by = db.Column(db.String(255))
    exabgp_id = db.Column(db.String(255), unique=True)  # ExaBGP rule identifier
    error_message = db.Column(db.Text)  # If status is ERROR
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='rule', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(FlowSpecRule, self).__init__(**kwargs)
        if not self.exabgp_id:
            self.exabgp_id = f"rule-{self.id}"
    
    def to_dict(self):
        """Convert rule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'match': {
                'source_ip': self.source_ip,
                'destination_ip': self.destination_ip,
                'protocol': self.protocol,
                'source_port': self.source_port,
                'destination_port': self.destination_port,
                'dscp': self.dscp,
                'fragment_offset': self.fragment_offset,
            },
            'action': self.action.value if self.action else None,
            'rate_limit_value': self.rate_limit_value,
            'status': self.status.value if self.status else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'withdrawn_at': self.withdrawn_at.isoformat() if self.withdrawn_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'exabgp_id': self.exabgp_id,
            'error_message': self.error_message,
        }
    
    def is_expired(self):
        """Check if rule has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_exabgp_format(self):
        """Convert rule to ExaBGP FlowSpec announcement format"""
        match_parts = []
        
        if self.destination_ip:
            match_parts.append(f"match destination {self.destination_ip}")
        if self.source_ip:
            match_parts.append(f"match source {self.source_ip}")
        if self.protocol:
            match_parts.append(f"match protocol {self.protocol}")
        if self.destination_port:
            match_parts.append(f"match destination-port {self.destination_port}")
        if self.source_port:
            match_parts.append(f"match source-port {self.source_port}")
        
        then_part = f"then {self.action.value}"
        if self.action == RuleAction.RATE_LIMIT and self.rate_limit_value:
            then_part = f"then rate-limit {self.rate_limit_value}"
        
        return {
            'type': 'flow',
            'scope': 'all',
            'flow': {
                'route': match_parts + [then_part]
            }
        }

class AuditLog(db.Model):
    """Audit log for rule changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = db.Column(db.String(36), db.ForeignKey('flowspec_rules.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # created, updated, deployed, withdrawn, deleted
    previous_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    details = db.Column(db.JSON)  # Additional details as JSON
    user = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'action': self.action,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'details': self.details,
            'user': self.user,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='operator')  # admin, operator, viewer
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
