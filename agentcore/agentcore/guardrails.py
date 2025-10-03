"""Guardrails integration for content filtering."""

from typing import Dict, Any
import boto3


class GuardrailsManager:
    """Manages Bedrock Guardrails for input/output filtering."""
    
    def __init__(
        self,
        bedrock_client,
        guardrail_id: str,
        guardrail_version: str = "DRAFT",
    ):
        """Initialize guardrails manager.
        
        Args:
            bedrock_client: Boto3 Bedrock client
            guardrail_id: Guardrail identifier
            guardrail_version: Guardrail version
        """
        self.client = bedrock_client
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
    
    def check_input(self, text: str) -> Dict[str, Any]:
        """Check input text against guardrails.
        
        Args:
            text: Input text to check
            
        Returns:
            Dict with 'allowed' boolean and optional 'reason'
        """
        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source="INPUT",
                content=[{"text": {"text": text}}],
            )
            
            action = response.get("action", "NONE")
            
            if action == "GUARDRAIL_INTERVENED":
                return {
                    "allowed": False,
                    "reason": "Content blocked by guardrails",
                    "assessments": response.get("assessments", []),
                }
            
            return {"allowed": True}
        
        except Exception as e:
            # Log error but allow by default
            print(f"Guardrail check error: {e}")
            return {"allowed": True}
    
    def check_output(self, text: str) -> Dict[str, Any]:
        """Check output text against guardrails.
        
        Args:
            text: Output text to check
            
        Returns:
            Dict with 'allowed' boolean and optional 'reason'
        """
        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source="OUTPUT",
                content=[{"text": {"text": text}}],
            )
            
            action = response.get("action", "NONE")
            
            if action == "GUARDRAIL_INTERVENED":
                return {
                    "allowed": False,
                    "reason": "Content blocked by guardrails",
                    "assessments": response.get("assessments", []),
                }
            
            return {"allowed": True}
        
        except Exception as e:
            # Log error but allow by default
            print(f"Guardrail check error: {e}")
            return {"allowed": True}
