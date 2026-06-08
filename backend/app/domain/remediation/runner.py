import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.domain.incidents.models import RemediationAction, RemediationStatus
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class CooldownActiveException(Exception):
    """Exception raised when a remediation action is blocked by active cooldown."""
    pass

class RemediationRunner:
    def __init__(self, db: Session):
        self.db = db

    def check_cooldown(self, action_name: str, target_resource: str, cooldown_minutes: int = 5, exclude_id: str = None) -> bool:
        """
        Checks if a remediation action was triggered for the target resource within the cooldown window.
        Returns True if execution is allowed, False if blocked by cooldown.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        
        query = self.db.query(RemediationAction).filter(
            RemediationAction.action_name == action_name,
            RemediationAction.target_resource == target_resource,
            RemediationAction.status.in_([
                RemediationStatus.APPROVED, 
                RemediationStatus.EXECUTING, 
                RemediationStatus.COMPLETED
            ]),
            RemediationAction.created_at >= cutoff_time
        )
        
        if exclude_id:
            query = query.filter(RemediationAction.id != exclude_id)
            
        recent_action = query.first()

        if recent_action:
            logger.warning(
                f"Remediation action '{action_name}' on '{target_resource}' blocked by active cooldown. "
                f"Recent execution {recent_action.id} was at {recent_action.created_at}."
            )
            return False
        return True


    def execute_action(self, action_name: str, target_resource: str, params: dict = None) -> bool:
        """
        Executes actual or mock remediation command.
        """
        logger.info(f"Executing remediation '{action_name}' on resource '{target_resource}' with params: {params}")
        
        # In mock or test environment, simulate success
        if settings.API_ENV in ("test", "development") or not settings.ENABLE_REMEDIATION:
            logger.info("Mock remediation execution succeeded.")
            return True
            
        try:
            # Here real systems would trigger a script or Kubernetes API call.
            # Example: Restarting a pod, rolling back deployment, scaling replica sets.
            # We log and simulate.
            return True
        except Exception as e:
            logger.error(f"Failed to execute remediation action: {e}")
            return False

    def validate_health(self, target_resource: str) -> bool:
        """
        Performs post-remediation health check to verify target resource health.
        """
        logger.info(f"Performing post-remediation health check on resource '{target_resource}'")
        
        if "fail-health" in target_resource:
            logger.info("Simulated health check failure.")
            return False
            
        # Example validation: Query K8s API or check Prometheus alerts
        # For our SRE pipeline, we simulate returning healthy.
        return True

