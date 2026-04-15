"""
Signal and trade performance analytics.

This module supports signal risk/reward analysis and closed-trade performance metrics.
"""

from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskRewardAnalysis:
    def __init__(self, signal: Dict):
        self.signal_type = signal.get("type", "UNKNOWN")
        self.entry = float(signal.get("entry", 0))
        self.stop_loss = float(signal.get("sl", 0))
        self.target = float(signal.get("target", 0))

    def get_risk(self) -> float:
        return abs(self.entry - self.stop_loss)

    def get_reward(self) -> float:
        return abs(self.target - self.entry)

    def get_risk_reward_ratio(self) -> float:
        risk = self.get_risk()
        reward = self.get_reward()
        if risk <= 0:
            return 0.0
        return round(reward / risk, 2)

    def to_dict(self) -> Dict:
        return {
            "entry": self.entry,
            "sl": self.stop_loss,
            "target": self.target,
            "risk": self.get_risk(),
            "reward": self.get_reward(),
            "risk_reward_ratio": self.get_risk_reward_ratio()
        }


def analyze_signal(signal: Optional[Dict]) -> Optional[RiskRewardAnalysis]:
    if not signal:
        return None

    try:
        return RiskRewardAnalysis(signal)
    except Exception as e:
        logger.error(f"Error analyzing signal: {str(e)}")
        return None


def get_analysis_text(signal: Optional[Dict]) -> str:
    analysis = analyze_signal(signal)
    if not analysis:
        return ""

    return f"""
╔════════════════════════════════════╗
║     RISK/REWARD ANALYSIS            ║
╚════════════════════════════════════╝

📊 Trade Setup:
  Type:              {signal.get('type', 'UNKNOWN')}
  Entry:             {analysis.entry:.2f}
  Stop Loss:         {analysis.stop_loss:.2f}
  Target:            {analysis.target:.2f}

💰 Risk/Reward:
  Risk:              {analysis.get_risk():.2f} points
  Reward:            {analysis.get_reward():.2f} points
  R/R Ratio:         1:{analysis.get_risk_reward_ratio():.2f}
"""


def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def analyze_trade_performance(trades: List[Dict]) -> Dict:
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

    closed_trades = [trade for trade in trades if trade.get("status") in {"WIN", "LOSS"}]
    total_trades = len(closed_trades)
    wins = 0
    losses = 0
    total_pnl = 0.0
    win_pnl = 0.0
    loss_pnl = 0.0

    for trade in closed_trades:
        pnl = _safe_float(trade.get("pnl", 0))
        total_pnl += pnl

        if trade.get("status") == "WIN":
            wins += 1
            win_pnl += pnl
        elif trade.get("status") == "LOSS":
            losses += 1
            loss_pnl += abs(pnl)

    win_rate = round((wins / total_trades) * 100, 2) if total_trades else 0.0
    avg_win = round((win_pnl / wins), 2) if wins else 0.0
    avg_loss = round((loss_pnl / losses), 2) if losses else 0.0
    risk_reward_ratio = round((avg_win / avg_loss), 2) if avg_loss else 0.0

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward_ratio": risk_reward_ratio
    }

