"""
Trading performance metrics calculation.

Calculates performance metrics from a list of completed trades:
- Total trades, wins, losses
- Win rate percentage
- Total P&L
- Average win/loss
- Risk/reward ratio
"""

from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Trade status constants
STATUS_PENDING = "PENDING"
STATUS_WIN = "WIN"
STATUS_LOSS = "LOSS"


def calculate_pnl(trade: Dict) -> Optional[float]:
    """
    Calculate P&L for a trade based on type and prices.
    
    Args:
        trade: Trade dict with type, entry, exit_price
        
    Returns:
        P&L in points, or None if insufficient data
        
    Calculation:
        BUY:  exit_price - entry_price
        SELL: entry_price - exit_price
    """
    try:
        trade_type = trade.get("type", "").upper()
        entry = float(trade.get("entry"))
        exit_price = float(trade.get("exit_price"))
        
        if trade_type == "BUY":
            return exit_price - entry
        elif trade_type == "SELL":
            return entry - exit_price
        else:
            logger.warning(f"Unknown trade type: {trade_type}")
            return None
            
    except (ValueError, TypeError) as e:
        logger.error(f"Error calculating P&L: {e}")
        return None


def calculate_metrics(trades: List[Dict]) -> Dict:
    """
    Calculate comprehensive trading performance metrics.
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with metrics:
            - total_trades: Number of closed trades (excludes PENDING)
            - wins: Number of winning trades
            - losses: Number of losing trades
            - win_rate: Percentage of winning trades
            - total_pnl: Sum of all P&L
            - avg_win: Average P&L per winning trade
            - avg_loss: Average P&L per losing trade (absolute value)
            - risk_reward_ratio: avg_win / avg_loss ratio
            
    Notes:
        - PENDING trades are excluded from calculations
        - Returns 0 or None for division by zero cases
        - All P&L values in points
    """
    
    if not trades:
        return _empty_metrics()
    
    # Filter to only closed trades
    closed_trades = [
        t for t in trades 
        if t.get("status", "").upper() != STATUS_PENDING
    ]
    
    if not closed_trades:
        return _empty_metrics()
    
    # Separate wins and losses
    winning_trades = [t for t in closed_trades if t.get("status", "").upper() == STATUS_WIN]
    losing_trades = [t for t in closed_trades if t.get("status", "").upper() == STATUS_LOSS]
    
    # Calculate P&L for each trade
    win_pnls = []
    loss_pnls = []
    total_pnl = 0.0
    
    for trade in closed_trades:
        # Try to use existing pnl field first
        if "pnl" in trade and trade["pnl"] is not None:
            pnl = float(trade["pnl"])
        else:
            # Calculate from prices
            pnl = calculate_pnl(trade)
            if pnl is None:
                logger.warning(f"Could not calculate P&L for trade {trade.get('id')}")
                continue
        
        total_pnl += pnl
        
        if trade.get("status", "").upper() == STATUS_WIN:
            win_pnls.append(pnl)
        elif trade.get("status", "").upper() == STATUS_LOSS:
            loss_pnls.append(abs(pnl))  # Store absolute value for loss
    
    # Calculate metrics
    total_trades = len(closed_trades)
    wins = len(winning_trades)
    losses = len(losing_trades)
    
    # Win rate
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    # Average win
    avg_win = (sum(win_pnls) / len(win_pnls)) if win_pnls else 0.0
    
    # Average loss (as positive number)
    avg_loss = (sum(loss_pnls) / len(loss_pnls)) if loss_pnls else 0.0
    
    # Risk/reward ratio
    risk_reward_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0
    
    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "risk_reward_ratio": round(risk_reward_ratio, 2),
    }


def _empty_metrics() -> Dict:
    """Return empty metrics dictionary (0 or None values)."""
    return {
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "total_pnl": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "risk_reward_ratio": 0.0,
    }


def get_metrics_summary(trades: List[Dict]) -> str:
    """
    Get a formatted string summary of trading metrics.
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Formatted string for display
        
    Example:
        📊 Trading Performance
        ─────────────────────
        Total: 25 | Wins: 17 | Losses: 8
        Win Rate: 68.0%
        Total P&L: +287.50 pts
        Avg Win: +16.91 pts | Avg Loss: -25.50 pts
        Risk/Reward: 0.66
    """
    metrics = calculate_metrics(trades)
    
    if metrics["total_trades"] == 0:
        return "📊 Trading Performance\n─────────────────────\nNo closed trades yet."
    
    pnl_sign = "+" if metrics["total_pnl"] >= 0 else ""
    color_emoji = "📈" if metrics["total_pnl"] >= 0 else "📉"
    
    summary = f"""📊 Trading Performance
─────────────────────
Total: {metrics['total_trades']} | Wins: {metrics['wins']} | Losses: {metrics['losses']}
Win Rate: {metrics['win_rate']}%
Total P&L: {color_emoji} {pnl_sign}{metrics['total_pnl']} pts
Avg Win: +{metrics['avg_win']} pts | Avg Loss: -{metrics['avg_loss']} pts
Risk/Reward: {metrics['risk_reward_ratio']}"""
    
    return summary


# Example usage
if __name__ == "__main__":
    # Example trades
    example_trades = [
        {
            "id": "trade_1",
            "type": "BUY",
            "entry": 100,
            "exit_price": 110,
            "status": "WIN",
            "pnl": 10
        },
        {
            "id": "trade_2",
            "type": "BUY",
            "entry": 100,
            "exit_price": 95,
            "status": "LOSS",
            "pnl": -5
        },
        {
            "id": "trade_3",
            "type": "SELL",
            "entry": 100,
            "exit_price": 90,
            "status": "WIN",
            "pnl": 10
        },
        {
            "id": "trade_4",
            "type": "BUY",
            "entry": 100,
            "exit_price": 100,
            "status": "PENDING",
            "pnl": None
        },
    ]
    
    metrics = calculate_metrics(example_trades)
    print("Metrics:", metrics)
    print("\nSummary:")
    print(get_metrics_summary(example_trades))
