"""
Performance analytics for closed trades.

This module summarizes a list of trades and computes key metrics
for win/loss performance and risk/reward.
"""

from typing import Dict, List

from utils.trade_storage import STATUS_LOSS, STATUS_PENDING, STATUS_WIN


def _normalize_trade_status(trade: Dict) -> str:
    """
    Normalize trade status from either status or outcome fields.
    """
    status = str(trade.get("status", "")).upper().strip()
    if status:
        return status

    outcome = str(trade.get("outcome", "")).upper().strip()
    if outcome == "WIN":
        return STATUS_WIN
    if outcome == "LOSS":
        return STATUS_LOSS
    if outcome == "OPEN":
        return STATUS_PENDING

    return ""


def _trade_pnl(trade: Dict) -> float:
    """
    Calculate trade PnL using trade type semantics.

    BUY -> exit - entry
    SELL -> entry - exit
    """
    trade_type = str(trade.get("type", "")).upper()
    entry = float(trade.get("entry", 0))
    exit_price = float(trade.get("exit_price", 0))

    if trade_type == "BUY":
        return exit_price - entry
    if trade_type == "SELL":
        return entry - exit_price

    return 0.0


def analyze_trade_performance(trades: List[Dict]) -> Dict[str, float]:
    """
    Analyze a list of trades and return performance summary.

    Args:
        trades: List of trade dictionaries

    Returns:
        Dictionary with performance metrics
    """
    total_trades = 0
    wins = 0
    losses = 0
    total_pnl = 0.0
    win_pnl = 0.0
    loss_pnl = 0.0

    for trade in trades:
        if not trade:
            continue

        status = _normalize_trade_status(trade)
        if status == STATUS_PENDING or status == "":
            continue

        if status not in {STATUS_WIN, STATUS_LOSS}:
            continue

        try:
            entry = float(trade.get("entry", 0))
            exit_price = float(trade.get("exit_price", 0))
        except (TypeError, ValueError):
            continue

        if entry == 0 or exit_price == 0:
            continue

        pnl = _trade_pnl(trade)
        total_trades += 1
        total_pnl += pnl

        if status == STATUS_WIN:
            wins += 1
            win_pnl += pnl
        elif status == STATUS_LOSS:
            losses += 1
            loss_pnl += abs(pnl)

    win_rate = round((wins / total_trades) * 100, 2) if total_trades else 0.0
    avg_win = round((win_pnl / wins), 2) if wins else 0.0
    avg_loss = round((loss_pnl / losses), 2) if losses else 0.0

    if avg_loss > 0:
        risk_reward_ratio = round(avg_win / avg_loss, 2)
    else:
        risk_reward_ratio = 0.0

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward_ratio": risk_reward_ratio,
    }
