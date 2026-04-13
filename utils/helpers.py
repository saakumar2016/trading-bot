from utils.logger import get_logger

logger = get_logger(__name__)

def val(x) -> float:
    """
    Safely convert value to float, handling numpy scalars.
    
    Args:
        x: Value to convert
        
    Returns:
        Float value
    """
    try:
        return float(x)
    except (ValueError, TypeError):
        try:
            return x.item()
        except Exception as e:
            logger.error(f"Failed to convert value {x}: {str(e)}")
            return 0.0