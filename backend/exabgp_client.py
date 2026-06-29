import socket
import json
import logging
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class ExaBGPClient:
    """Client for communicating with ExaBGP"""
    
    def __init__(self, host: str = None, port: int = None, timeout: int = None):
        self.host = host or Config.EXABGP_HOST
        self.port = port or Config.EXABGP_PORT
        self.timeout = timeout or Config.EXABGP_TIMEOUT
    
    def connect(self) -> socket.socket:
        """Establish connection to ExaBGP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            logger.info(f"Connected to ExaBGP at {self.host}:{self.port}")
            return sock
        except Exception as e:
            logger.error(f"Failed to connect to ExaBGP: {e}")
            raise
    
    def announce_rule(self, rule_data: Dict) -> bool:
        """
        Announce a FlowSpec rule to ExaBGP
        
        Args:
            rule_data: Rule data in ExaBGP format
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sock = self.connect()
            message = json.dumps(rule_data) + "\n"
            sock.sendall(message.encode())
            
            # Read response
            response = sock.recv(4096).decode()
            sock.close()
            
            logger.info(f"Rule announced successfully: {rule_data.get('flow', {}).get('route')}")
            return True
        except Exception as e:
            logger.error(f"Failed to announce rule: {e}")
            return False
    
    def withdraw_rule(self, rule_id: str) -> bool:
        """
        Withdraw a FlowSpec rule from ExaBGP
        
        Args:
            rule_id: Rule ID to withdraw
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sock = self.connect()
            withdraw_msg = {
                'type': 'flow',
                'scope': 'withdraw',
                'flow': {
                    'route': rule_id
                }
            }
            message = json.dumps(withdraw_msg) + "\n"
            sock.sendall(message.encode())
            
            # Read response
            response = sock.recv(4096).decode()
            sock.close()
            
            logger.info(f"Rule withdrawn successfully: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to withdraw rule: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if ExaBGP is reachable"""
        try:
            sock = self.connect()
            sock.close()
            return True
        except:
            return False

class FastNetMonClient:
    """Client for communicating with FastNetMon API"""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or Config.FASTNETMON_API_URL
    
    def announce_flowspec(self, rule_data: Dict) -> bool:
        """
        Announce a FlowSpec rule via FastNetMon API
        
        Args:
            rule_data: Rule data to announce
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import requests
            
            endpoint = f"{self.api_url}/api/v1/flowspec/announce/"
            response = requests.post(
                endpoint,
                json=rule_data,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"FlowSpec rule announced via FastNetMon: {rule_data}")
                return True
            else:
                logger.error(f"FastNetMon API error: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to announce rule via FastNetMon: {e}")
            return False
    
    def withdraw_flowspec(self, rule_id: str) -> bool:
        """
        Withdraw a FlowSpec rule via FastNetMon API
        
        Args:
            rule_id: Rule ID to withdraw
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import requests
            
            endpoint = f"{self.api_url}/api/v1/flowspec/withdraw/{rule_id}"
            response = requests.delete(
                endpoint,
                timeout=5
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"FlowSpec rule withdrawn via FastNetMon: {rule_id}")
                return True
            else:
                logger.error(f"FastNetMon API error: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to withdraw rule via FastNetMon: {e}")
            return False
