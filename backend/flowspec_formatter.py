import json

class ExaBGPFlowSpecFormatter:
    """
    Format FlowSpec rules for ExaBGP and validation.
    """
    
    @staticmethod
    def validate_rule(rule_data: dict) -> tuple[bool, str]:
        """
        Validate FlowSpec rule data.
        
        Args:
            rule_data: Rule dictionary
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # At least one match criteria required
        match_fields = ['source_ip', 'destination_ip', 'protocol', 
                       'source_port', 'destination_port']
        
        has_match = any(rule_data.get(field) for field in match_fields)
        if not has_match:
            return False, "At least one match criteria is required"
        
        # Validate IPs if provided
        if rule_data.get('source_ip'):
            if not ExaBGPFlowSpecFormatter._is_valid_cidr(rule_data['source_ip']):
                return False, f"Invalid source IP: {rule_data['source_ip']}"
        
        if rule_data.get('destination_ip'):
            if not ExaBGPFlowSpecFormatter._is_valid_cidr(rule_data['destination_ip']):
                return False, f"Invalid destination IP: {rule_data['destination_ip']}"
        
        # Validate ports
        if rule_data.get('source_port'):
            if not ExaBGPFlowSpecFormatter._is_valid_port(rule_data['source_port']):
                return False, f"Invalid source port: {rule_data['source_port']}"
        
        if rule_data.get('destination_port'):
            if not ExaBGPFlowSpecFormatter._is_valid_port(rule_data['destination_port']):
                return False, f"Invalid destination port: {rule_data['destination_port']}"
        
        return True, ""
    
    @staticmethod
    def _is_valid_cidr(cidr: str) -> bool:
        """Validate CIDR notation"""
        try:
            from ipaddress import ip_network
            ip_network(cidr, strict=False)
            return True
        except:
            return False
    
    @staticmethod
    def _is_valid_port(port_spec: str) -> bool:
        """Validate port specification"""
        try:
            parts = port_spec.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range
                    start, end = part.split('-')
                    start, end = int(start.strip()), int(end.strip())
                    if not (0 <= start <= 65535 and 0 <= end <= 65535 and start <= end):
                        return False
                else:
                    # Single port
                    port = int(part)
                    if not (0 <= port <= 65535):
                        return False
            return True
        except:
            return False
