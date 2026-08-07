from datetime import date
from models.trade import Trade
from collections import defaultdict

def get_trades_between(user_id, start_date, end_date):

    trades = (
        Trade.query
        .filter(
            Trade.user_id == user_id,
            Trade.trade_date >=start_date,
            Trade.trade_date <= end_date
        )
        .order_by(
            Trade.trade_date,
            Trade.trade_time
        )
        .all()
    )

    return trades

def calculate_accuracy(trades):

    if len(trades) == 0:
        return 0
    
    profitable = sum(
        1 for trade in trades if trade.is_profit
    )

    accuracy = (profitable / len(trades)) * 100

    return round(accuracy,2)

def calculate_pnl(trades):

    if len(trades) == 0:
        return 0
    
    total_pnl = sum(
        trade.amount for trade in trades
    )

    return round(total_pnl, 2)

def calculate_plan_discipline(trades):

    if len(trades) == 0:
        return {
            "percentage":0,
            "followed":0,
            "broken":0
        }
    
    followed = sum(
        1 for trade in trades if  trade.followed_plan
    )

    broken = len(trades) - followed

    percentage = round(
        (followed / len(trades)) * 100,2)

    return {
        "percentage": percentage,
        "followed":followed,
        "broken":broken
    }

def calculate_best_worst_day(trades):

    if len(trades) == 0:
        return None, None
    
    daily_pnl = defaultdict(float)

    for trade in trades:
        daily_pnl[trade.trade_date] += float(trade.amount)

    best_day = max(
        daily_pnl,
        key=daily_pnl.get
    )

    worst_day = min(
        daily_pnl,
        key=daily_pnl.get
    )

    best = {
        "date":best_day,
        "pnl":daily_pnl[best_day]
    }

    worst = {
        "date": worst_day,
        "pnl": daily_pnl[worst_day]
    }

    return best, worst

def calculate_trading_hours(trades):

    hours = defaultdict(list)

    for trade in trades:

        if trade.trade_time is None:
            continue

        hour = trade.trade_time.hour

        hours[hour].append(trade)

    result = []

    for hour in sorted(hours.keys()):

        hour_trades = hours[hour]

        total = len(hour_trades)

        profitable = sum(
            1 for trade in hour_trades
            if trade.is_profit
        )

        pnl = sum(
            trade.amount
            for trade in hour_trades
        )

        avg_pnl = pnl / total

        accuracy = (
            profitable / total
        )* 100

        result.append({
            "hour":hour,
            "trades":total,
            "accuracy":round(accuracy,2),
            "avg_pnl":round(avg_pnl,2)
        })

    return result

from collections import defaultdict

def get_daily_pnl(trades):

    daily = defaultdict(float)

    for trade in trades:
        daily[trade.trade_date] += float(trade.amount)

    result = []

    for trade_date in sorted(daily.keys()):

        result.append({
            "date": trade_date.strftime("%d %b"),
            "pnl": round(daily[trade_date], 2)
        })

    return result

def get_equity_curve(trades):

    running_total = 0

    result = []

    for trade in trades:

        running_total += float(trade.amount)

        result.append({

            "date": trade.trade_date.strftime("%d %b"),

            "equity": round(running_total, 2)

        })

    return result

def calculate_max_drawdown(trades):

    if not trades:
        return 0

    running_total = 0
    peak = 0
    max_drawdown = 0

    for trade in trades:

        running_total += float(trade.amount)

        if running_total > peak:
            peak = running_total

        drawdown = peak - running_total

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return round(max_drawdown, 2)

def calculate_trade_statistics(trades):

    profitable = [
        float(trade.amount)
        for trade in trades
        if trade.is_profit
    ]

    losing = [
        abs(float(trade.amount))
        for trade in trades
        if not trade.is_profit
    ]

    average_win = (
        round(sum(profitable) / len(profitable), 2)
        if profitable else 0
    )

    average_loss = (
        round(sum(losing) / len(losing), 2)
        if losing else 0
    )

    gross_profit = sum(profitable)
    gross_loss = sum(losing)

    profit_factor = (
        round(gross_profit / gross_loss, 2)
        if gross_loss > 0 else 0
    )

    risk_reward = (
        round(average_win / average_loss, 2)
        if average_loss > 0 else 0
    )

    return {
        "average_win": average_win,
        "average_loss": average_loss,
        "profit_factor": profit_factor,
        "risk_reward": risk_reward
    }