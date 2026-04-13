"""
Backtesting engine for strategy validation and performance analysis.
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger
from core.trend import get_trend
from core.levels import get_levels
from core.strategy import check_signal

logger = get_logger(__name__)


class BacktestResult:
    """Container for backtesting results."""
    
    def __init__(self):
        self.signals: List[Dict] = []
        self.trades: List[Dict] = []
        self.total_signals = 0
        self.total_trades = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.max_win = 0.0
        self.max_loss = 0.0
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary for display."""
        return {
            "Total Signals": self.total_signals,
            "Total Trades": self.total_trades,
            "Wins": self.win_count,
            "Losses": self.loss_count,
            "Win Rate %": f"{self.win_rate:.2f}%",
            "Total Profit": f"{self.total_profit:.2f}",
            "Total Loss": f"{self.total_loss:.2f}",
            "Net P&L": f"{(self.total_profit - self.total_loss):.2f}",
            "Profit Factor": f"{self.profit_factor:.2f}",
            "Avg Win": f"{self.avg_win:.2f}",
            "Avg Loss": f"{self.avg_loss:.2f}",
            "Max Win": f"{self.max_win:.2f}",
            "Max Loss": f"{self.max_loss:.2f}"
        }


def run_backtest(df: pd.DataFrame, symbol: str = "NSEI") -> BacktestResult:
    """
    Run backtest on historical data.
    
    Args:
        df: Historical OHLC data
        symbol: Trading symbol for logging
        
    Returns:
        BacktestResult with performance metrics
    """
    result = BacktestResult()
    
    try:
        if len(df) < 100:
            logger.warning(f"Insufficient data for backtest: {len(df)} rows")
            return result
        
        logger.info(f"Starting backtest for {symbol} with {len(df)} candles")
        
        # Slide through data to generate signals
        for i in range(80, len(df)):
            window = df.iloc[:i+1]
            
            try:
                trend = get_trend(window)
                signal = check_signal(window, trend)
                
                if signal:
                    result.total_signals += 1
                    current_price = float(window['Close'].iloc[-1])
                    
                    # Simulate trade execution
                    trade = {
                        "index": i,
                        "timestamp": window.index[-1],
                        "price": current_price,
                        "type": signal["type"],
                        "entry": signal["entry"],
                        "sl": signal["sl"],
                        "target": signal["target"],
                        "trend": signal.get("trend", "UNKNOWN")
                    }
                    
                    # Check if target or SL would be hit in next 5 candles
                    if i + 5 < len(df):
                        future_prices = df.iloc[i+1:i+6]['Close'].values
                        
                        for future_price in future_prices:
                            if signal["type"] == "BUY":
                                if future_price >= signal["target"]:
                                    profit = signal["target"] - signal["entry"]
                                    trade["outcome"] = "Win"
                                    trade["exit_price"] = signal["target"]
                                    trade["pnl"] = profit
                                    result.win_count += 1
                                    result.total_profit += profit
                                    result.max_win = max(result.max_win, profit)
                                    if result.avg_win > 0:
                                        result.avg_win = (result.avg_win + profit) / 2
                                    else:
                                        result.avg_win = profit
                                    break
                                elif future_price <= signal["sl"]:
                                    loss = signal["entry"] - signal["sl"]
                                    trade["outcome"] = "Loss"
                                    trade["exit_price"] = signal["sl"]
                                    trade["pnl"] = -loss
                                    result.loss_count += 1
                                    result.total_loss += loss
                                    result.max_loss = max(result.max_loss, loss)
                                    if result.avg_loss > 0:
                                        result.avg_loss = (result.avg_loss + loss) / 2
                                    else:
                                        result.avg_loss = loss
                                    break
                            else:  # SELL
                                if future_price <= signal["target"]:
                                    profit = signal["entry"] - signal["target"]
                                    trade["outcome"] = "Win"
                                    trade["exit_price"] = signal["target"]
                                    trade["pnl"] = profit
                                    result.win_count += 1
                                    result.total_profit += profit
                                    result.max_win = max(result.max_win, profit)
                                    if result.avg_win > 0:
                                        result.avg_win = (result.avg_win + profit) / 2
                                    else:
                                        result.avg_win = profit
                                    break
                                elif future_price >= signal["sl"]:
                                    loss = signal["sl"] - signal["entry"]
                                    trade["outcome"] = "Loss"
                                    trade["exit_price"] = signal["sl"]
                                    trade["pnl"] = -loss
                                    result.loss_count += 1
                                    result.total_loss += loss
                                    result.max_loss = max(result.max_loss, loss)
                                    if result.avg_loss > 0:
                                        result.avg_loss = (result.avg_loss + loss) / 2
                                    else:
                                        result.avg_loss = loss
                                    break
                        else:
                            trade["outcome"] = "Open"
                    
                    result.trades.append(trade)
                    result.total_trades += 1
                    
            except Exception as e:
                logger.debug(f"Error processing candle {i}: {str(e)}")
                continue
        
        # Calculate metrics
        if result.total_trades > 0:
            result.win_rate = (result.win_count / result.total_trades) * 100
            
        if result.total_loss > 0:
            result.profit_factor = result.total_profit / result.total_loss
        
        logger.info(f"Backtest complete: {result.total_signals} signals, {result.total_trades} trades, "
                   f"{result.win_rate:.1f}% win rate")
        
        return result
        
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}", exc_info=True)
        return result


def get_backtest_text_summary(result: BacktestResult) -> str:
    """Generate text summary of backtest results."""
    summary = """
╔════════════════════════════════════╗
║      BACKTEST PERFORMANCE SUMMARY   ║
╚════════════════════════════════════╝

📊 Signals & Trades:
  Total Signals:    {total_signals}
  Total Trades:     {total_trades}
  Win Count:        {win_count}
  Loss Count:       {loss_count}

💰 Profitability:
  Total Profit:     ${total_profit:.2f}
  Total Loss:       ${total_loss:.2f}
  Net P&L:          ${net_pnl:.2f}
  Profit Factor:    {profit_factor:.2f}x

📈 Performance:
  Win Rate:         {win_rate:.2f}%
  Avg Win:          ${avg_win:.2f}
  Avg Loss:         ${avg_loss:.2f}
  Max Win:          ${max_win:.2f}
  Max Loss:         ${max_loss:.2f}
""".format(
        total_signals=result.total_signals,
        total_trades=result.total_trades,
        win_count=result.win_count,
        loss_count=result.loss_count,
        total_profit=result.total_profit,
        total_loss=result.total_loss,
        net_pnl=result.total_profit - result.total_loss,
        profit_factor=result.profit_factor if result.profit_factor > 0 else 0,
        win_rate=result.win_rate,
        avg_win=result.avg_win,
        avg_loss=result.avg_loss,
        max_win=result.max_win,
        max_loss=result.max_loss
    )
    return summary
