from datetime import date, timedelta


from models.trade import Trade


from sqlalchemy import func


from extensions import db


from calendar import monthrange








def get_recent_trades(user_id):


    trades = (


        Trade.query


        .filter_by(user_id=user_id)


        .order_by(Trade.trade_date.desc(),


                  Trade.trade_time.desc())


        .limit(10)


        .all() 


    )





    return trades





def get_current_trading_week():





    today = date.today()





    monday = today - timedelta(days=today.weekday())





    friday = monday + timedelta(days=4)





    return monday, friday








def get_weekly_trade_count(user_id):


    


    monday , friday = get_current_trading_week()





    count = (


        Trade.query.filter(


            Trade.user_id == user_id,


            Trade.trade_date >= monday,


            Trade.trade_date <= friday


        )


        .count()


    )





    return count





def get_weekly_pnl(user_id):


    


    monday , friday = get_current_trading_week()





    total = (


        db.session.query(


            func.sum(Trade.amount)


        )


        .filter(


            Trade.user_id == user_id,


            Trade.trade_date >=  monday,


            Trade.trade_date <= friday


        )


        .scalar()


    )





    return total if total else 0





def get_weekly_accuracy(user_id):


    monday , friday = get_current_trading_week()





    total_trades = (


        Trade.query


        .filter(


            Trade.user_id == user_id,


            Trade.trade_date >= monday,


            Trade.trade_date <= friday


        )


        .count()


    )


    if total_trades == 0:


        return 0


    


    profitable_trades = (


        Trade.query


        .filter(


            Trade.user_id == user_id,


            Trade.trade_date >=monday,


            Trade.trade_date <= friday,


            Trade.is_profit == True


        )


        .count()


    )





    accuracy = (profitable_trades / total_trades) * 100





    return round(accuracy, 1)





def group_trades_by_day(user_id):





    trades = (
    Trade.query
    .filter(
        Trade.user_id == user_id
    )
    .order_by(
        Trade.trade_date.desc(),
        Trade.trade_time.desc()
    )
    .all()
)


    grouped = {}





    for trade in trades:





        if trade.trade_date not in grouped:


            grouped[trade.trade_date] = []





        grouped[trade.trade_date].append(trade)





    return grouped





def is_successful_day(day_trades):


    


    followed = 0


    not_followed = 0





    for trade  in day_trades:





        if trade.followed_plan:


            followed+=1


        else:


            not_followed+=1


        


    return followed > not_followed





def summarize_day(day_trades):


    trade_count = len(day_trades)





    pnl = 0

    for trade in day_trades:

        if trade.is_profit:
            pnl += trade.amount
        else:
            pnl -= trade.amount





    if trade_count == 0:


        status = "no_trade"





    elif is_successful_day(day_trades):


        status = "success"





    else:


        status = "failure"





    return {


        "trades":trade_count,


        "pnl":pnl,


        "status":status


    }





def get_monthly_calendar(user_id, year, month):





    grouped_trades = group_trades_by_day(user_id)





    calendar_cells = []





    total_days = monthrange(year, month)[1]





    first_weekday = date(year,month,1).weekday()





    today = date.today()





    for _ in range (first_weekday):


        calendar_cells.append(None)





    for day in range(1, total_days+1):


        current_date = date(year, month, day)





        if current_date > today:


            info={


                "trades":0,


                "pnl":0,


                "status":"future"


            }





        elif current_date.weekday() >= 5:


            info={


                "status":"weekend"


            }





        else:


            info=summarize_day(


                grouped_trades.get(current_date, [])


            )





        calendar_cells.append(


            {


                "date":current_date,


                "info":info


            }


        )





    return calendar_cells





    





def get_current_streak(user_id):


    


    grouped_trades = group_trades_by_day(user_id)





    streak = 0





    current_day = date.today()





    if not grouped_trades:
       return 0

    earliest_day = min(grouped_trades.keys())

    while current_day >= earliest_day:





        if current_day.weekday() >= 5:


            current_day -= timedelta(days=1)


            continue





        if current_day not in grouped_trades:


            current_day -= timedelta(days=1)


            continue





        if is_successful_day(grouped_trades[current_day]):


            streak += 1


            current_day -= timedelta(days=1)


        else:


            break





    return streak





def get_day_details(user_id,selected_date):


    


    trades = (


        Trade.query


        .filter_by(


            user_id=user_id,


            trade_date=selected_date


        )


        .order_by(Trade.trade_time)


        .all()


    )


    return trades





def get_day_summary(user_id, selected_date):





    trades = get_day_details(user_id, selected_date)





    if not trades:


        return None


    


    total_trades = len(trades)





    total_pnl = sum(
    trade.amount if trade.is_profit else -trade.amount
    for trade in trades
    )


    


    profitable_trades = sum(


        1 for trade in trades if trade.is_profit


    )





    followed_trades = sum(


        1 for trade in trades if trade.followed_plan


    )





    accuracy = round(


        (profitable_trades / total_trades) * 100,


        2


    )





    followed_percentage = round(


        (followed_trades / total_trades) * 100,


        2


    )





    status = "Successful Day" if is_successful_day(trades) else "Failed Day"





    return{


        "total_trades":total_trades,


        "total_pnl":total_pnl,


        "accuracy":accuracy,


        "followed_percentage":followed_percentage,


        "status":status
    }