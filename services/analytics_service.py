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