"""
Performance analytics for trading system.

This module provides comprehensive performance analysis for trade data.
"""

from typing import Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)


def analyze_trade_performance(trades: List[Dict]) -> Dict:
    """
    Analyze trade performance metrics, ignoring PENDING trades.

    Args:
        trades: List of trade dictionaries

    Returns:
        Dictionary with performance metrics:
        - total_trades: Total number of closed trades
        - wins: Number of winning trades
        - losses: Number of losing trades
        - win_rate: Win rate percentage
        - total_pnl: Total profit/loss in points
        - avg_win: Average win in points
        - avg_loss: Average loss in points
        - risk_reward_ratio: Average win / average loss ratio
    """
    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "risk_reward_ratio": 0.0
        }

    # Filter out PENDING trades
    closed_trades = [t for t in trades if t.get('status') != 'PENDING']

    if not closed_trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "risk_reward_ratio": 0.0
        }

    total_trades = len(closed_trades)
    wins = 0
    losses = 0
    total_pnl = 0.0
    win_pnl_sum = 0.0
    loss_pnl_sum = 0.0

    for trade in closed_trades:
        try:
            pnl = trade.get('pnl', 0)
            if pnl is None:
                continue

            total_pnl += pnl

            if trade.get('status') == 'WIN':
                wins += 1
                win_pnl_sum += pnl
            elif trade.get('status') == 'LOSS':
                losses += 1
                loss_pnl_sum += abs(pnl)  # Loss P&L is negative, but we want positive for averaging

        except (TypeError, ValueError) as e:
            logger.warning(f"Error processing trade {trade.get('id', 'unknown')}: {str(e)}")
            continue

    # Calculate metrics
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    avg_win = (win_pnl_sum / wins) if wins > 0 else 0.0
    avg_loss = (loss_pnl_sum / losses) if losses > 0 else 0.0
    risk_reward_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "risk_reward_ratio": round(risk_reward_ratio, 2)
    }
