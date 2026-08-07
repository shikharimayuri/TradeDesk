from flask import Flask,render_template, request
from config import Config
from extensions import db, bcrypt
from login_manager import login_manager
from routes.auth import auth
from flask_login import login_required, current_user
from models.user import User
from models.trade import Trade
from flask_migrate import Migrate
from routes.trade import trade
from calendar import monthrange, month_name
from datetime import date,datetime
from services.dashboard_service import (
    get_recent_trades,
    get_weekly_trade_count,
    get_weekly_pnl,
    get_weekly_accuracy,
    get_current_streak,
    get_monthly_calendar,
    get_day_details,
    get_day_summary,
    get_weekly_pnl_graph,
    get_weekly_accuracy_graph,
    get_weekly_win_loss,
    get_weekly_trade_graph
)
from services.analytics_service import (
    get_trades_between,
    calculate_accuracy,
    calculate_pnl,
    calculate_plan_discipline,
    calculate_best_worst_day,
    calculate_trading_hours,
    get_daily_pnl,
    get_equity_curve,
    calculate_trade_statistics,
    calculate_max_drawdown
)

app=Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app,db)

app.register_blueprint(auth)
app.register_blueprint(trade)

@app.route("/")
def home():

    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():

    recent_trades = get_recent_trades(current_user.id)
    print("RECENT:", recent_trades)

    weekly_trade_count = get_weekly_trade_count(current_user.id)
    print("WEEKLY COUNT:", weekly_trade_count)

    weekly_pnl = get_weekly_pnl(current_user.id)

    weekly_pnl_graph = get_weekly_pnl_graph(current_user.id)

    weekly_accuracy_graph = get_weekly_accuracy_graph(current_user.id)

    weekly_win_loss = get_weekly_win_loss(current_user.id)

    weekly_accuracy = get_weekly_accuracy(current_user.id)

    weekly_trade_graph = get_weekly_trade_graph(current_user.id)

    wins = weekly_win_loss["wins"]
  
    losses = weekly_win_loss["losses"]

    current_streak = get_current_streak(current_user.id)
    print("CURRENT STREAK:", current_streak)

    today = date.today()

    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)
    selected = request.args.get("selected")

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    calendar_data = get_monthly_calendar(
        current_user.id,
        year,
        month
    )

    print("CALENDAR CELLS:", len(calendar_data))
    print("FIRST 10 CELLS:")
    for cell in calendar_data[:10]:
        print(cell)

    selected_date = None

    if selected:
        selected_date = datetime.strptime(
            selected,
            "%Y-%m-%d"
        ).date()

    day_details = []
    day_summary = None

    if selected_date:
        day_details = get_day_details(
            current_user.id,
            selected_date
        )

        day_summary = get_day_summary(
            current_user.id,
            selected_date
        )

    return render_template(
        "dashboard.html",
        recent_trades=recent_trades,
        weekly_trade_count=weekly_trade_count,
        weekly_pnl=weekly_pnl,
        weekly_accuracy=weekly_accuracy,
        wins=wins,
        losses=losses,
        current_streak=current_streak,
        calendar_data=calendar_data,
        current_month=month_name[month],
        current_month_number=month,
        current_year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        selected_date=selected_date,
        day_details=day_details,
        day_summary=day_summary,
        weekly_pnl_graph=weekly_pnl_graph,
        weekly_accuracy_graph = weekly_accuracy_graph,
        weekly_win_loss=weekly_win_loss,
        weekly_trade_graph=weekly_trade_graph,
    )

@app.route("/analytics")

@login_required

def analytics():
    today = date.today()



    start = request.args.get(

        "start",

            default=today.replace(day=1).strftime("%Y-%m-%d")

    )



    end = request.args.get(

        "end",

        default=today.strftime("%Y-%m-%d")

    )



    start_date = datetime.strptime(

        start,

        "%Y-%m-%d"

    ).date()



    end_date = datetime.strptime(

        end,

        "%Y-%m-%d"

    ).date()



    trades = get_trades_between(
    current_user.id,
    start_date,
    end_date
)

    accuracy = calculate_accuracy(trades)

    total_pnl = calculate_pnl(trades)

    trade_stats = calculate_trade_statistics(trades)

    print("\n------ ANALYTICS TRADES ------")

    for trade in trades:
        print(
        trade.trade_date,
        trade.amount,
        trade.is_profit
    )

    print("Analytics Total:", total_pnl)
    print("-----------------------------\n")

    plan_discipline = calculate_plan_discipline(trades)

    best_day,worst_day = calculate_best_worst_day(trades)

    trading_hours = calculate_trading_hours(
        trades
    )
    daily_pnl = get_daily_pnl(trades)

    equity_curve = get_equity_curve(trades)
    
    max_drawdown = calculate_max_drawdown(trades)

    return render_template(
        "analytics.html",
        trades=trades,
        accuracy=accuracy,
        total_pnl=total_pnl,
        plan_discipline=plan_discipline,
        best_day=best_day,
        worst_day=worst_day,
        trading_hours=trading_hours,
        daily_pnl=daily_pnl,
        start=start,
        end=end,
        equity_curve=equity_curve,
        trade_stats=trade_stats,
        max_drawdown=max_drawdown
    )

if __name__=="__main__":
    app.run(debug=True)