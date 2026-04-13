"""
Risk and reward analysis for trading signals.
"""
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskRewardAnalysis:
    """
    Analyze risk/reward metrics for a trade signal.
    
    Attributes:
        entry: Entry price
        stop_loss: Stop loss price
        target: Target/take profit price
        type: Trade type (BUY/SELL)
    """
    
    def __init__(self, signal: Dict):
        """
        Initialize from a signal dictionary.
        
        Args:
            signal: Signal dict with entry, sl, target, type
        """
        self.entry = float(signal.get("entry", 0))
        self.stop_loss = float(signal.get("sl", 0))
        self.target = float(signal.get("target", 0))
        self.signal_type = signal.get("type", "UNKNOWN")
        
        if self.entry <= 0:
            logger.warning("Invalid entry price")
    
    def get_risk(self) -> float:
        """
        Calculate risk (distance from entry to stop loss).
        
        Returns:
            Risk in points
        """
        return abs(self.entry - self.stop_loss)
    
    def get_reward(self) -> float:
        """
        Calculate reward (distance from entry to target).
        
        Returns:
            Reward in points
        """
        return abs(self.target - self.entry)
    
    def get_risk_reward_ratio(self) -> float:
        """
        Calculate risk/reward ratio.
        
        Returns:
            Ratio of reward:risk (higher is better, min 1.0)
        """
        risk = self.get_risk()
        reward = self.get_reward()
        
        if risk <= 0:
            logger.warning("Risk is 0 or negative")
            return 0.0
        
        return round(reward / risk, 2)
    
    def get_breakeven_win_rate(self) -> float:
        """
        Calculate win rate needed to break even.
        
        For breakeven: wins * reward = losses * risk
        If win_rate is W, then (W * reward) = ((1-W) * risk)
        W = risk / (risk + reward)
        
        Returns:
            Win rate percentage needed to break even
        """
        risk = self.get_risk()
        reward = self.get_reward()
        
        if risk + reward <= 0:
            return 50.0
        
        breakeven_rate = (risk / (risk + reward)) * 100
        return round(breakeven_rate, 2)
    
    def get_position_quality_score(self) -> float:
        """
        Calculate overall position quality (0-100).
        
        Considers:
        - Risk/reward ratio (best: 1:3)
        - Win rate needed
        
        Returns:
            Quality score 0-100
        """
        rr_ratio = self.get_risk_reward_ratio()
        breakeven_wr = self.get_breakeven_win_rate()
        
        # Ideal RR is 1:3 or better
        rr_score = min((rr_ratio / 3.0) * 50, 50)  # Max 50 points
        
        # Ideal breakeven WR is <50% (easier to achieve)
        wr_score = max(0, (100 - breakeven_wr) / 2)  # Max 50 points
        
        return round(rr_score + wr_score, 2)
    
    def get_quality_rating(self) -> str:
        """
        Get quality rating based on position quality score.
        
        Returns:
            Rating: "Excellent", "Good", "Fair", or "Poor"
        """
        score = self.get_position_quality_score()
        
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def to_dict(self) -> Dict:
        """
        Convert analysis to dictionary.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "Entry": f"{self.entry:.2f}",
            "Stop Loss": f"{self.stop_loss:.2f}",
            "Target": f"{self.target:.2f}",
            "Risk": f"{self.get_risk():.2f}",
            "Reward": f"{self.get_reward():.2f}",
            "RR Ratio": f"1:{self.get_risk_reward_ratio():.2f}",
            "Breakeven Win %": f"{self.get_breakeven_win_rate():.2f}%",
            "Quality Score": f"{self.get_position_quality_score():.1f}/100",
            "Rating": self.get_quality_rating()
        }


def analyze_signal(signal: Optional[Dict]) -> Optional[RiskRewardAnalysis]:
    """
    Analyze a trading signal for risk/reward metrics.
    
    Args:
        signal: Signal dictionary or None
        
    Returns:
        RiskRewardAnalysis or None if signal is invalid
    """
    if not signal:
        return None
    
    try:
        return RiskRewardAnalysis(signal)
    except Exception as e:
        logger.error(f"Error analyzing signal: {str(e)}")
        return None


def get_analysis_text(signal: Optional[Dict]) -> str:
    """
    Get formatted text analysis of signal.
    
    Args:
        signal: Signal dictionary or None
        
    Returns:
        Formatted text analysis or empty string
    """
    analysis = analyze_signal(signal)
    
    if not analysis:
        return ""
    
    return f"""
╔════════════════════════════════════╗
║     RISK/REWARD ANALYSIS            ║
╚════════════════════════════════════╝

📊 Trade Setup:
  Type:              {signal['type']}
  Entry:             {analysis.entry:.2f}
  Stop Loss:         {analysis.stop_loss:.2f}
  Target:            {analysis.target:.2f}

💰 Risk/Reward:
  Risk:              {analysis.get_risk():.2f} points
  Reward:            {analysis.get_reward():.2f} points
  R/R Ratio:         1:{analysis.get_risk_reward_ratio():.2f}

📈 Statistics:
  Breakeven Win %:   {analysis.get_breakeven_win_rate():.2f}%
  Quality Score:     {analysis.get_position_quality_score():.1f}/100
  Rating:            {analysis.get_quality_rating()}
"""
