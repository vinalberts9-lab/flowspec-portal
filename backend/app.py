import os
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from config import config
from models import db, FlowSpecRule, AuditLog, User, RuleStatus, RuleAction
from exabgp_client import ExaBGPClient, FastNetMonClient
from juniper_flowspec import JuniperFlowSpecGenerator

# Initialize Flask app
app = Flask(__name__)
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
JWTManager(app)
CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))

# Initialize clients
exabgp_client = ExaBGPClient()
fastnetmon_client = FastNetMonClient()
juniper_generator = JuniperFlowSpecGenerator()

# Configure logging
logging.basicConfig(
    level=app.config.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables on startup
with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
    if User.query.filter_by(username='admin').first() is None:
        admin = User(
            username='admin',
            email='admin@flowspec-portal.local',
            password_hash=generate_password_hash('admin'),
            role='admin',
            enabled=True
        )
        db.session.add(admin)
        db.session.commit()
        logger.info("Default admin user created (username: admin, password: admin)")

def require_role(*roles):
    """Decorator to check user role"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            user = User.query.filter_by(username=identity).first()
            if not user or user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def log_audit(rule_id: str, action: str, user: str = None, previous_status: str = None, new_status: str = None, details: dict = None):
    """Log audit trail"""
    audit = AuditLog(
        rule_id=rule_id,
        action=action,
        user=user or get_jwt_identity(),
        previous_status=previous_status,
        new_status=new_status,
        details=details or {},
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.enabled:
        return jsonify({'error': 'User account is disabled'}), 403
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    access_token = create_access_token(identity=username)
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/register', methods=['POST'])
@require_role('admin')
def register():
    """Register new user (admin only)"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'operator')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        enabled=True
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

# ============================================================================
# RULES ROUTES
# ============================================================================

@app.route('/api/rules', methods=['POST'])
@require_role('admin', 'operator')
def create_rule():
    """Create a new FlowSpec rule"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Rule name is required'}), 400
    
    # Create rule
    rule = FlowSpecRule(
        name=data.get('name'),
        description=data.get('description'),
        source_ip=data.get('source_ip'),
        destination_ip=data.get('destination_ip'),
        protocol=data.get('protocol'),
        source_port=data.get('source_port'),
        destination_port=data.get('destination_port'),
        dscp=data.get('dscp'),
        fragment_offset=data.get('fragment_offset'),
        action=data.get('action', 'discard'),
        rate_limit_value=data.get('rate_limit_value'),
        enabled=data.get('enabled', True),
        created_by=get_jwt_identity(),
        status=RuleStatus.DRAFT
    )
    
    # Set expiration if TTL provided
    if data.get('ttl_minutes'):
        ttl = min(int(data.get('ttl_minutes')), app.config['MAX_RULE_TTL_MINUTES'])
        rule.expires_at = datetime.utcnow() + timedelta(minutes=ttl)
    
    db.session.add(rule)
    db.session.commit()
    
    log_audit(rule.id, 'created', details={'name': rule.name})
    
    return jsonify(rule.to_dict()), 201

@app.route('/api/rules', methods=['GET'])
@jwt_required()
def list_rules():
    """List all rules"""
    status = request.args.get('status')
    enabled = request.args.get('enabled')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = FlowSpecRule.query
    
    if status:
        query = query.filter_by(status=status)
    if enabled is not None:
        query = query.filter_by(enabled=enabled.lower() == 'true')
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'rules': [rule.to_dict() for rule in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200

@app.route('/api/rules/<rule_id>', methods=['GET'])
@jwt_required()
def get_rule(rule_id):
    """Get rule details"""
    rule = FlowSpecRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify(rule.to_dict()), 200

@app.route('/api/rules/<rule_id>', methods=['PUT'])
@require_role('admin', 'operator')
def update_rule(rule_id):
    """Update a rule"""
    rule = FlowSpecRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    if rule.status != RuleStatus.DRAFT:
        return jsonify({'error': 'Can only update draft rules'}), 400
    
    data = request.get_json()
    
    # Update fields
    for field in ['name', 'description', 'source_ip', 'destination_ip', 'protocol', 
                   'source_port', 'destination_port', 'dscp', 'fragment_offset', 
                   'action', 'rate_limit_value', 'enabled']:
        if field in data:
            setattr(rule, field, data[field])
    
    if 'ttl_minutes' in data and data['ttl_minutes']:
        ttl = min(int(data['ttl_minutes']), app.config['MAX_RULE_TTL_MINUTES'])
        rule.expires_at = datetime.utcnow() + timedelta(minutes=ttl)
    
    db.session.commit()
    log_audit(rule.id, 'updated')
    
    return jsonify(rule.to_dict()), 200

@app.route('/api/rules/<rule_id>/deploy', methods=['POST'])
@require_role('admin', 'operator')
def deploy_rule(rule_id):
    """Deploy a rule to ExaBGP/Juniper"""
    rule = FlowSpecRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    if rule.status == RuleStatus.ACTIVE:
        return jsonify({'error': 'Rule is already active'}), 400
    
    try:
        # Generate Juniper FlowSpec rule
        juniper_rule = juniper_generator.generate_rule(rule)
        
        # Announce via ExaBGP
        exabgp_rule = rule.to_exabgp_format()
        success = exabgp_client.announce_rule(exabgp_rule)
        
        if success:
            rule.status = RuleStatus.ACTIVE
            rule.deployed_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(rule.id, 'deployed', 
                     previous_status=RuleStatus.DRAFT.value,
                     new_status=RuleStatus.ACTIVE.value,
                     details={'juniper_rule': juniper_rule})
            
            return jsonify({
                'message': 'Rule deployed successfully',
                'rule': rule.to_dict(),
                'juniper_config': juniper_rule
            }), 200
        else:
            rule.status = RuleStatus.ERROR
            rule.error_message = 'Failed to announce rule to ExaBGP'
            db.session.commit()
            
            return jsonify({
                'error': 'Failed to deploy rule',
                'details': rule.error_message
            }), 500
    except Exception as e:
        rule.status = RuleStatus.ERROR
        rule.error_message = str(e)
        db.session.commit()
        
        logger.error(f"Error deploying rule: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to deploy rule',
            'details': str(e)
        }), 500

@app.route('/api/rules/<rule_id>/withdraw', methods=['POST'])
@require_role('admin', 'operator')
def withdraw_rule(rule_id):
    """Withdraw a rule"""
    rule = FlowSpecRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    if rule.status != RuleStatus.ACTIVE:
        return jsonify({'error': 'Can only withdraw active rules'}), 400
    
    try:
        success = exabgp_client.withdraw_rule(rule.exabgp_id)
        
        if success:
            rule.status = RuleStatus.WITHDRAWN
            rule.withdrawn_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(rule.id, 'withdrawn',
                     previous_status=RuleStatus.ACTIVE.value,
                     new_status=RuleStatus.WITHDRAWN.value)
            
            return jsonify({
                'message': 'Rule withdrawn successfully',
                'rule': rule.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Failed to withdraw rule'}), 500
    except Exception as e:
        logger.error(f"Error withdrawing rule: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to withdraw rule',
            'details': str(e)
        }), 500

@app.route('/api/rules/<rule_id>', methods=['DELETE'])
@require_role('admin')
def delete_rule(rule_id):
    """Delete a rule"""
    rule = FlowSpecRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    if rule.status == RuleStatus.ACTIVE:
        return jsonify({'error': 'Cannot delete active rule. Withdraw first'}), 400
    
    rule_name = rule.name
    db.session.delete(rule)
    db.session.commit()
    
    log_audit(rule_id, 'deleted', details={'name': rule_name})
    
    return jsonify({'message': 'Rule deleted successfully'}), 200

# ============================================================================
# PREVIEW ROUTES
# ============================================================================

@app.route('/api/rules/preview/juniper', methods=['POST'])
@jwt_required()
def preview_juniper():
    """Preview Juniper configuration for a rule"""
    data = request.get_json()
    
    try:
        # Create temporary rule object for preview
        rule = FlowSpecRule(
            name=data.get('name', 'preview-rule'),
            destination_ip=data.get('destination_ip'),
            source_ip=data.get('source_ip'),
            protocol=data.get('protocol'),
            destination_port=data.get('destination_port'),
            source_port=data.get('source_port'),
            action=data.get('action', 'discard')
        )
        
        juniper_config = juniper_generator.generate_rule(rule)
        
        return jsonify({
            'juniper_config': juniper_config
        }), 200
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return jsonify({
            'error': 'Failed to generate preview',
            'details': str(e)
        }), 400

@app.route('/api/rules/preview/exabgp', methods=['POST'])
@jwt_required()
def preview_exabgp():
    """Preview ExaBGP JSON for a rule"""
    data = request.get_json()
    
    try:
        rule = FlowSpecRule(
            name=data.get('name', 'preview-rule'),
            destination_ip=data.get('destination_ip'),
            source_ip=data.get('source_ip'),
            protocol=data.get('protocol'),
            destination_port=data.get('destination_port'),
            source_port=data.get('source_port'),
            action=data.get('action', 'discard')
        )
        
        exabgp_config = rule.to_exabgp_format()
        
        return jsonify(exabgp_config), 200
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return jsonify({
            'error': 'Failed to generate preview',
            'details': str(e)
        }), 400

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Get dashboard statistics"""
    total_rules = FlowSpecRule.query.count()
    active_rules = FlowSpecRule.query.filter_by(status=RuleStatus.ACTIVE).count()
    draft_rules = FlowSpecRule.query.filter_by(status=RuleStatus.DRAFT).count()
    error_rules = FlowSpecRule.query.filter_by(status=RuleStatus.ERROR).count()
    
    # Check ExaBGP health
    exabgp_healthy = exabgp_client.health_check()
    
    return jsonify({
        'total_rules': total_rules,
        'active_rules': active_rules,
        'draft_rules': draft_rules,
        'error_rules': error_rules,
        'exabgp_status': 'healthy' if exabgp_healthy else 'unreachable',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/dashboard/active-rules', methods=['GET'])
@jwt_required()
def active_rules():
    """Get active rules"""
    rules = FlowSpecRule.query.filter_by(status=RuleStatus.ACTIVE).all()
    return jsonify([rule.to_dict() for rule in rules]), 200

# ============================================================================
# AUDIT LOG ROUTES
# ============================================================================

@app.route('/api/audit-logs', methods=['GET'])
@require_role('admin', 'operator')
def get_audit_logs():
    """Get audit logs"""
    rule_id = request.args.get('rule_id')
    action = request.args.get('action')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = AuditLog.query
    
    if rule_id:
        query = query.filter_by(rule_id=rule_id)
    if action:
        query = query.filter_by(action=action)
    
    paginated = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [log.to_dict() for log in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
