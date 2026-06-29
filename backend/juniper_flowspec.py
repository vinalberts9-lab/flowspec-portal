from datetime import timedelta
from models import FlowSpecRule, RuleAction
import logging

logger = logging.getLogger(__name__)

class JuniperFlowSpecGenerator:
    """
    Generate valid Juniper FlowSpec configuration from FlowSpec rules.
    Supports:
    - Juniper MX Series (MX480, MX960, etc.)
    - Juniper PTX Series
    - Juniper SRX Series
    """
    
    def __init__(self):
        self.version = "1.0"
    
    def generate_rule(self, rule: FlowSpecRule) -> str:
        """
        Generate a complete Juniper FlowSpec configuration block.
        
        Args:
            rule: FlowSpecRule object
            
        Returns:
            str: Juniper JunOS configuration
        """
        config_lines = []
        
        # Header comment
        config_lines.append(f"# FlowSpec Rule: {rule.name}")
        config_lines.append(f"# Description: {rule.description or 'N/A'}")
        config_lines.append(f"# Created: {rule.created_at}")
        config_lines.append("")
        
        # Determine rule name (sanitized)
        rule_name = self._sanitize_name(rule.name)
        
        # Build match criteria
        match_parts = self._build_match_criteria(rule)
        
        # Build then action
        then_action = self._build_then_action(rule)
        
        # Build the policy configuration
        config_lines.append("set policy-options policy-statement " + rule_name)
        config_lines.append("    term 1 {")
        
        # Add match criteria
        config_lines.append("        from {")
        for match in match_parts:
            config_lines.append(f"            {match}")
        config_lines.append("        }")
        
        # Add then action
        config_lines.append("        then {")
        for action in then_action:
            config_lines.append(f"            {action}")
        config_lines.append("        }")
        config_lines.append("    }")
        config_lines.append("}")
        config_lines.append("")
        
        # Add BGP export policy configuration
        config_lines.extend(self._build_bgp_flowspec_config(rule_name))
        
        return "\n".join(config_lines)
    
    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize rule name for Juniper configuration.
        Only alphanumeric and hyphens allowed.
        """
        sanitized = "".join(c if c.isalnum() or c == '-' else '_' for c in name)
        return sanitized[:32]  # Max 32 chars
    
    def _build_match_criteria(self, rule: FlowSpecRule) -> list:
        """
        Build match criteria lines for Juniper configuration.
        """
        matches = []
        
        if rule.destination_ip:
            matches.append(f"flow destination {rule.destination_ip}")
        
        if rule.source_ip:
            matches.append(f"flow source {rule.source_ip}")
        
        if rule.protocol:
            protocol_num = self._get_protocol_number(rule.protocol)
            matches.append(f"flow protocol {protocol_num}")
        
        if rule.destination_port:
            matches.append(f"flow destination-port {self._format_ports(rule.destination_port)}")
        
        if rule.source_port:
            matches.append(f"flow source-port {self._format_ports(rule.source_port)}")
        
        if rule.dscp is not None:
            matches.append(f"flow dscp {rule.dscp}")
        
        if rule.fragment_offset is not None:
            matches.append(f"flow fragment-offset {rule.fragment_offset}")
        
        return matches
    
    def _build_then_action(self, rule: FlowSpecRule) -> list:
        """
        Build then action lines for Juniper configuration.
        """
        actions = []
        
        if rule.action == RuleAction.DISCARD:
            actions.append("discard")
            actions.append("routing-instance flowspec-discard")
        elif rule.action == RuleAction.ACCEPT:
            actions.append("accept")
        elif rule.action == RuleAction.RATE_LIMIT:
            if rule.rate_limit_value:
                # Rate limit in kbps
                actions.append(f"policer FLOWSPEC_POLICER_{rule.rate_limit_value}")
                actions.append("accept")
            else:
                actions.append("accept")
        
        actions.append("as-path-prepend 0")
        return actions
    
    def _get_protocol_number(self, protocol: str) -> int:
        """
        Convert protocol name to number.
        """
        protocol_map = {
            'tcp': 6,
            'udp': 17,
            'icmp': 1,
            'igmp': 2,
            'ggp': 3,
            'ip': 0,
            'st': 5,
            'egp': 8,
            'igp': 9,
            'pup': 12,
            'ipcv': 71,
            'xtp': 36,
        }
        return protocol_map.get(protocol.lower(), 0)
    
    def _format_ports(self, ports: str) -> str:
        """
        Format ports for Juniper configuration.
        Handles: single port, comma-separated, ranges.
        """
        port_str = ""
        
        if ',' in ports:
            # Multiple ports
            port_list = [p.strip() for p in ports.split(',')]
            port_str = "[ " + " ".join(port_list) + " ]"
        elif '-' in ports:
            # Port range
            port_str = ports  # Juniper uses same format: 1024-2048
        else:
            # Single port
            port_str = ports
        
        return port_str
    
    def _build_bgp_flowspec_config(self, rule_name: str) -> list:
        """
        Build BGP FlowSpec export policy configuration.
        """
        config = [
            "# BGP FlowSpec Export Configuration",
            "set protocols bgp export " + rule_name,
            "set protocols bgp group <BGP_GROUP_NAME> family inet flow",
            "set protocols bgp group <BGP_GROUP_NAME> local-preference 100",
            "",
        ]
        return config
    
    def generate_complete_config(self, rules: list) -> str:
        """
        Generate a complete Juniper configuration with multiple rules.
        
        Args:
            rules: List of FlowSpecRule objects
            
        Returns:
            str: Complete Juniper configuration
        """
        config_lines = []
        
        # Header
        config_lines.append("# Juniper FlowSpec Configuration")
        config_lines.append(f"# Generated by FlowSpec Portal v{self.version}")
        config_lines.append(f"# Date: {self._get_timestamp()}")
        config_lines.append("# WARNING: Review carefully before deploying")
        config_lines.append("")
        
        # Add all rules
        for rule in rules:
            config_lines.append(self.generate_rule(rule))
            config_lines.append("".join(["="] * 80))
            config_lines.append("")
        
        # Add BGP configuration template
        config_lines.extend(self._get_bgp_template())
        
        return "\n".join(config_lines)
    
    def generate_discard_routing_instance(self) -> str:
        """
        Generate Juniper routing-instance configuration for discard action.
        Required for DISCARD action to work properly.
        """
        config = [
            "# Discard Routing Instance Configuration",
            "set routing-instances flowspec-discard instance-type virtual-router",
            "set routing-instances flowspec-discard routing-options static route 0.0.0.0/0 discard",
            "",
        ]
        return "\n".join(config)
    
    def generate_policer_config(self, rate_limit_kbps: int) -> str:
        """
        Generate Juniper policer configuration for rate-limiting.
        
        Args:
            rate_limit_kbps: Rate limit in kilobits per second
            
        Returns:
            str: Juniper policer configuration
        """
        config = [
            f"# Policer Configuration for {rate_limit_kbps}kbps",
            f"set firewall policer FLOWSPEC_POLICER_{rate_limit_kbps} if-exceeding bandwidth-limit {rate_limit_kbps}k",
            f"set firewall policer FLOWSPEC_POLICER_{rate_limit_kbps} if-exceeding burst-limit-bytes 125000",
            f"set firewall policer FLOWSPEC_POLICER_{rate_limit_kbps} then discard",
            "",
        ]
        return "\n".join(config)
    
    def _get_bgp_template(self) -> list:
        """
        Get template for BGP FlowSpec configuration.
        """
        template = [
            "# BGP FlowSpec Configuration Template",
            "# Replace <BGP_GROUP_NAME> with your actual BGP group name",
            "# Replace <PEER_IP> with your BGP peer IP",
            "",
            "# set routing-options autonomous-system <YOUR_ASN>",
            "# set protocols bgp group <BGP_GROUP_NAME> type internal",
            "# set protocols bgp group <BGP_GROUP_NAME> local-address <YOUR_IP>",
            "# set protocols bgp group <BGP_GROUP_NAME> neighbor <PEER_IP>",
            "# set protocols bgp group <BGP_GROUP_NAME> family inet flow",
            "# set protocols bgp group <BGP_GROUP_NAME> family inet unicast",
            "",
            "# IMPORTANT: Ensure your routers support FlowSpec",
            "# MX Series: Supported on MXSeries with Trio chipset",
            "# PTX Series: Supported",
            "# SRX Series: Limited support (check documentation)",
            "",
        ]
        return template
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
