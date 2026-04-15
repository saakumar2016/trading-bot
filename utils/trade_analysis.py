import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

TRADES_FILE = os.path.expanduser("~/.streamlit_trades/trades.csv")


class TradeAnalyzer:
    """Analyze trade patterns, identify issues, suggest improvements."""
    
    def __init__(self):
        self.trades = []
        self.df = None
    
    def load_trades(self) -> bool:
        """Load trades from CSV."""
        try:
            if not os.path.exists(TRADES_FILE):
                logger.warning("No trade file found")
                return False
            
            self.df = pd.read_csv(TRADES_FILE)
            self.trades = self.df.to_dict('records')
            logger.info(f"Loaded {len(self.trades)} trades")
            return len(self.trades) > 0
        except Exception as e:
            logger.error(f"Error loading trades: {str(e)}")
            return False
    
    def get_closed_trades(self) -> List[Dict]:
        """Get only closed trades."""
        closed_statuses = ['WIN', 'LOSS', 'TIMEOUT']
        return [t for t in self.trades if t.get('status') in closed_statuses]
    
    def calculate_basic_stats(self) -> Dict:
        """Calculate win rate, pnl, etc."""
        closed = self.get_closed_trades()
        
        if not closed:
            return {}
        
        wins = len([t for t in closed if t.get('status') == 'WIN'])
        losses = len([t for t in closed if t.get('status') == 'LOSS'])
        timeouts = len([t for t in closed if t.get('status') == 'TIMEOUT'])
        
        total = len(closed)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        total_pnl = sum(float(t.get('pnl', 0)) for t in closed if t.get('pnl'))
        
        win_pnl = sum(float(t.get('pnl', 0)) for t in closed if t.get('status') == 'WIN' and t.get('pnl'))
        loss_pnl = sum(abs(float(t.get('pnl', 0))) for t in closed if t.get('status') == 'LOSS' and t.get('pnl'))
        
        avg_win = win_pnl / wins if wins > 0 else 0
        avg_loss = loss_pnl / losses if losses > 0 else 0
        
        return {
            'total_closed': total,
            'wins': wins,
            'losses': losses,
            'timeouts': timeouts,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'win_loss_ratio': round(avg_win / avg_loss, 2) if avg_loss > 0 else 0
        }
    
    def analyze_by_type(self) -> Dict:
        """Analyze BUY vs SELL performance."""
        closed = self.get_closed_trades()
        
        buy_trades = [t for t in closed if t.get('type') == 'BUY']
        sell_trades = [t for t in closed if t.get('type') == 'SELL']
        
        stats = {}
        
        for trade_type, trades in [('BUY', buy_trades), ('SELL', sell_trades)]:
            if not trades:
                continue
            
            wins = len([t for t in trades if t.get('status') == 'WIN'])
            total = len(trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            total_pnl = sum(float(t.get('pnl', 0)) for t in trades if t.get('pnl'))
            
            stats[trade_type] = {
                'count': total,
                'wins': wins,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2)
            }
        
        return stats
    
    def analyze_by_trend(self) -> Dict:
        """Analyze UP vs DOWN vs SIDEWAYS trend performance."""
        closed = self.get_closed_trades()
        
        trends = set(t.get('trend', 'UNKNOWN') for t in closed)
        stats = {}
        
        for trend in trends:
            trend_trades = [t for t in closed if t.get('trend') == trend]
            if not trend_trades:
                continue
            
            wins = len([t for t in trend_trades if t.get('status') == 'WIN'])
            total = len(trend_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            total_pnl = sum(float(t.get('pnl', 0)) for t in trend_trades if t.get('pnl'))
            
            stats[trend] = {
                'count': total,
                'wins': wins,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2)
            }
        
        return stats
    
    def analyze_risk_reward(self) -> Dict:
        """Analyze risk/reward ratios."""
        closed = self.get_closed_trades()
        
        metrics = {
            'rr_ratios': [],
            'profitable_high_rr': 0,
            'losing_low_rr': 0,
            'breakdown': {}
        }
        
        for trade in closed:
            try:
                entry = float(trade.get('entry', 0))
                sl = float(trade.get('sl', 0))
                target = float(trade.get('target', 0))
                pnl = float(trade.get('pnl', 0))
                status = trade.get('status')
                
                if entry == 0:
                    continue
                
                risk = abs(entry - sl)
                reward = abs(target - entry)
                
                if risk > 0:
                    rr_ratio = reward / risk
                    metrics['rr_ratios'].append(rr_ratio)
                    
                    if status == 'WIN' and rr_ratio >= 1.5:
                        metrics['profitable_high_rr'] += 1
                    elif status == 'LOSS' and rr_ratio < 1.2:
                        metrics['losing_low_rr'] += 1
            
            except (ValueError, TypeError):
                continue
        
        avg_rr = sum(metrics['rr_ratios']) / len(metrics['rr_ratios']) if metrics['rr_ratios'] else 0
        
        return {
            'avg_rr_ratio': round(avg_rr, 2),
            'profitable_high_rr': metrics['profitable_high_rr'],
            'losing_low_rr': metrics['losing_low_rr'],
            'rr_trades_analyzed': len(metrics['rr_ratios'])
        }
    
    def identify_failure_patterns(self) -> List[Dict]:
        """Identify where trades fail most."""
        closed = self.get_closed_trades()
        losses = [t for t in closed if t.get('status') == 'LOSS']
        
        if not losses:
            return []
        
        patterns = {
            'wrong_trend': [],
            'bad_rr': [],
            'quick_loss': [],
            'timeout_loss': []
        }
        
        for trade in losses:
            try:
                trade_type = trade.get('type')
                trend = trade.get('trend')
                entry = float(trade.get('entry', 0))
                sl = float(trade.get('sl', 0))
                target = float(trade.get('target', 0))
                pnl = float(trade.get('pnl', 0))
                status = trade.get('status')
                
                # Wrong trend: SELL in UP or BUY in DOWN
                if (trade_type == 'SELL' and trend == 'UP') or (trade_type == 'BUY' and trend == 'DOWN'):
                    patterns['wrong_trend'].append(trade)
                
                # Bad RR: risk greater than reward
                if entry != 0:
                    risk = abs(entry - sl)
                    reward = abs(target - entry)
                    if risk > 0 and reward / risk < 1.1:
                        patterns['bad_rr'].append(trade)
                
                # Quick loss: hit stop loss immediately (large negative pnl)
                if pnl < -15:
                    patterns['quick_loss'].append(trade)
                
                # Timeout loss
                if status == 'TIMEOUT':
                    patterns['timeout_loss'].append(trade)
            
            except (ValueError, TypeError):
                continue
        
        return [
            {'pattern': 'WRONG_TREND', 'count': len(patterns['wrong_trend']), 'trades': patterns['wrong_trend']},
            {'pattern': 'BAD_RR', 'count': len(patterns['bad_rr']), 'trades': patterns['bad_rr']},
            {'pattern': 'QUICK_LOSS', 'count': len(patterns['quick_loss']), 'trades': patterns['quick_loss']},
            {'pattern': 'TIMEOUT_LOSS', 'count': len(patterns['timeout_loss']), 'trades': patterns['timeout_loss']}
        ]
    
    def identify_win_patterns(self) -> List[Dict]:
        """Identify where trades win most."""
        closed = self.get_closed_trades()
        wins = [t for t in closed if t.get('status') == 'WIN']
        
        if not wins:
            return []
        
        patterns = {
            'strong_trend': [],
            'high_rr': [],
            'quick_win': [],
            'support_bounces': []
        }
        
        for trade in wins:
            try:
                trade_type = trade.get('type')
                trend = trade.get('trend')
                entry = float(trade.get('entry', 0))
                sl = float(trade.get('sl', 0))
                target = float(trade.get('target', 0))
                pnl = float(trade.get('pnl', 0))
                
                # Strong trend: BUY in UP or SELL in DOWN
                if (trade_type == 'BUY' and trend == 'UP') or (trade_type == 'SELL' and trend == 'DOWN'):
                    patterns['strong_trend'].append(trade)
                
                # High RR: reward significantly greater than risk
                if entry != 0:
                    risk = abs(entry - sl)
                    reward = abs(target - entry)
                    if risk > 0 and reward / risk >= 1.5:
                        patterns['high_rr'].append(trade)
                
                # Quick win: hit target fast (large positive pnl)
                if pnl > 10:
                    patterns['quick_win'].append(trade)
                
                # Support/Resistance bounces (inferred from setup)
                if trade_type == 'BUY':
                    patterns['support_bounces'].append(trade)
            
            except (ValueError, TypeError):
                continue
        
        return [
            {'pattern': 'STRONG_TREND', 'count': len(patterns['strong_trend']), 'trades': patterns['strong_trend']},
            {'pattern': 'HIGH_RR', 'count': len(patterns['high_rr']), 'trades': patterns['high_rr']},
            {'pattern': 'QUICK_WIN', 'count': len(patterns['quick_win']), 'trades': patterns['quick_win']},
            {'pattern': 'SUPPORT_BOUNCES', 'count': len(patterns['support_bounces']), 'trades': patterns['support_bounces']}
        ]
    
    def suggest_improvements(self) -> List[Dict]:
        """Suggest improvements based on analysis."""
        stats = self.calculate_basic_stats()
        by_type = self.analyze_by_type()
        by_trend = self.analyze_by_trend()
        rr_analysis = self.analyze_risk_reward()
        failures = self.identify_failure_patterns()
        
        suggestions = []
        
        # Check win rate
        if stats.get('win_rate', 0) < 50:
            suggestions.append({
                'issue': 'Low Win Rate',
                'value': f"{stats.get('win_rate', 0):.1f}%",
                'impact': 'HIGH',
                'actions': [
                    'Filter signals with stricter entry conditions',
                    'Only trade strong wick rejections (>50% wick ratio)',
                    'Require price to close > entry before confirming'
                ]
            })
        
        # Check for asymmetric payoff
        avg_win = stats.get('avg_win', 0)
        avg_loss = abs(stats.get('avg_loss', 0))
        if avg_win < avg_loss:
            suggestions.append({
                'issue': 'Asymmetric Payoff',
                'value': f"Avg Win: {avg_win:.2f}, Avg Loss: {avg_loss:.2f}",
                'impact': 'HIGH',
                'actions': [
                    'Increase target size (currently 30% of range)',
                    'Reduce stop-loss buffer (currently 10 points)',
                    'Use wider targets in high-volatility markets'
                ]
            })
        
        # Check for wrong trend entries
        wrong_trend_pattern = next((p for p in failures if p['pattern'] == 'WRONG_TREND'), None)
        if wrong_trend_pattern and wrong_trend_pattern['count'] > 0:
            suggestions.append({
                'issue': 'Trading Against Trend',
                'value': f"{wrong_trend_pattern['count']} trades",
                'impact': 'HIGH',
                'actions': [
                    'Disable SELL signals in UP trend',
                    'Disable BUY signals in DOWN trend',
                    'Only allow entries in trend direction or SIDEWAYS'
                ]
            })
        
        # Check BUY vs SELL performance
        for trade_type in ['BUY', 'SELL']:
            type_stats = by_type.get(trade_type, {})
            if type_stats.get('win_rate', 0) < 40 and type_stats.get('count', 0) > 5:
                suggestions.append({
                    'issue': f'{trade_type} Trades Underperforming',
                    'value': f"{type_stats.get('win_rate', 0):.1f}% win rate",
                    'impact': 'MEDIUM',
                    'actions': [
                        f'Review {trade_type} entry logic',
                        f'Tighten {trade_type} confirmation filters',
                        f'Temporarily disable {trade_type} signals for testing'
                    ]
                })
        
        # Check for timeout losses
        timeout_pattern = next((p for p in failures if p['pattern'] == 'TIMEOUT_LOSS'), None)
        if timeout_pattern and timeout_pattern['count'] > 0:
            suggestions.append({
                'issue': 'Stuck Trades (Timeout Losses)',
                'value': f"{timeout_pattern['count']} trades",
                'impact': 'MEDIUM',
                'actions': [
                    'Reduce timeout from 30 min to 15 min',
                    'Close trades at breakeven if stuck > 10 min',
                    'Add tighter profit-taking levels'
                ]
            })
        
        # Check quick losses
        quick_loss_pattern = next((p for p in failures if p['pattern'] == 'QUICK_LOSS'), None)
        if quick_loss_pattern and quick_loss_pattern['count'] > 0:
            quick_losses_pct = (quick_loss_pattern['count'] / stats.get('total_closed', 1)) * 100
            if quick_losses_pct > 20:
                suggestions.append({
                    'issue': 'Frequent Quick Stops (Whipsaws)',
                    'value': f"{quick_loss_pattern['count']} trades",
                    'impact': 'MEDIUM',
                    'actions': [
                        'Reduce SL_BUFFER from 10 to 5 points',
                        'Require stronger wick rejection (increase WICK_RATIO)',
                        'Increase MIN_RANGE_FILTER to reduce choppy market entries'
                    ]
                })
        
        return suggestions
    
    def generate_report(self) -> str:
        """Generate full analysis report."""
        if not self.load_trades():
            return "No trades to analyze"
        
        stats = self.calculate_basic_stats()
        by_type = self.analyze_by_type()
        by_trend = self.analyze_by_trend()
        rr_analysis = self.analyze_risk_reward()
        failures = self.identify_failure_patterns()
        wins = self.identify_win_patterns()
        suggestions = self.suggest_improvements()
        
        report = []
        report.append("=" * 70)
        report.append("TRADING SYSTEM ANALYSIS REPORT")
        report.append("=" * 70)
        
        # Overall Stats
        report.append("\n📊 OVERALL PERFORMANCE")
        report.append("-" * 70)
        for key, value in stats.items():
            report.append(f"  {key.upper():.<50} {value}")
        
        # By Trade Type
        report.append("\n🎯 PERFORMANCE BY TRADE TYPE")
        report.append("-" * 70)
        for trade_type, type_stats in by_type.items():
            report.append(f"\n  {trade_type}:")
            for key, value in type_stats.items():
                report.append(f"    {key:.<45} {value}")
        
        # By Trend
        report.append("\n📈 PERFORMANCE BY TREND")
        report.append("-" * 70)
        for trend, trend_stats in by_trend.items():
            report.append(f"\n  {trend}:")
            for key, value in trend_stats.items():
                report.append(f"    {key:.<45} {value}")
        
        # Risk/Reward Analysis
        report.append("\n⚖️ RISK/REWARD ANALYSIS")
        report.append("-" * 70)
        for key, value in rr_analysis.items():
            report.append(f"  {key.upper():.<50} {value}")
        
        # Failure Patterns
        report.append("\n❌ FAILURE PATTERNS")
        report.append("-" * 70)
        for pattern in failures:
            if pattern['count'] > 0:
                report.append(f"  {pattern['pattern']:.<50} {pattern['count']}")
        
        # Win Patterns
        report.append("\n✅ WIN PATTERNS")
        report.append("-" * 70)
        for pattern in wins:
            if pattern['count'] > 0:
                report.append(f"  {pattern['pattern']:.<50} {pattern['count']}")
        
        # Suggestions
        report.append("\n💡 IMPROVEMENT SUGGESTIONS")
        report.append("-" * 70)
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"\n  {i}. {suggestion['issue']} [{suggestion['impact']}]")
                report.append(f"     Current: {suggestion['value']}")
                report.append(f"     Actions:")
                for action in suggestion['actions']:
                    report.append(f"       • {action}")
        else:
            report.append("  No major issues detected - System performing well!")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)


def analyze_trades_and_print() -> Optional[str]:
    """Convenience function to analyze and print report."""
    analyzer = TradeAnalyzer()
    return analyzer.generate_report()
