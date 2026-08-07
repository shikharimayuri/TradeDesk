from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from extensions import db
from models.trade import Trade
from datetime import datetime, date, time, timedelta

trade = Blueprint("trade", __name__)

def is_consecutive(d1, d2):
    """
    Determines if two dates are consecutive, accounting for weekends
    (i.e., Friday to Monday is considered consecutive).
    """
    if d1 > d2:
        d1, d2 = d2, d1
    
    diff = (d2 - d1).days
    if diff <= 1:
        return True
    
    # If d1 is Friday (4) and d2 is Monday (0) and gap is 3 days
    if d1.weekday() == 4 and d2.weekday() == 0 and diff <= 3:
        return True
    
    # If d1 is Saturday (5) or Sunday (6) and d2 is Monday (0)
    if d1.weekday() in (5, 6) and d2.weekday() == 0 and diff <= 2:
        return True
        
    return False

def calculate_streaks(trades):
    """
    Calculates the current streak and longest streak of disciplined trading days.
    A day is disciplined if the user logged at least one trade and ALL trades on
    that day followed the plan (followed_plan == True).
    """
    if not trades:
        return 0, 0

    # Group trades by date to determine if each day was disciplined
    daily_status = {}
    for t in trades:
        d = t.trade_date
        if d not in daily_status:
            daily_status[d] = True
        # If any trade on this day did not follow the plan, the whole day is undisciplined
        if t.followed_plan is False:
            daily_status[d] = False

    # Sort the unique trading dates ascending
    sorted_dates = sorted(daily_status.keys())
    
    streaks = []
    current_streak_dates = []
    
    for d in sorted_dates:
        if daily_status[d]: # Disciplined day
            if not current_streak_dates:
                current_streak_dates.append(d)
            else:
                last_d = current_streak_dates[-1]
                if is_consecutive(last_d, d):
                    current_streak_dates.append(d)
                else:
                    streaks.append(current_streak_dates)
                    current_streak_dates = [d]
        else: # Undisciplined day breaks the streak
            if current_streak_dates:
                streaks.append(current_streak_dates)
                current_streak_dates = []
                
    if current_streak_dates:
        streaks.append(current_streak_dates)
        
    # Longest streak is the max length of any compiled streak
    longest_streak = max(len(s) for s in streaks) if streaks else 0
    
    # Current streak calculation
    current_streak = 0
    if streaks and sorted_dates:
        last_trade_date = sorted_dates[-1]
        today = date.today()
        
        # Check if the streak is still active (i.e. the last trade was today, yesterday, or over the weekend)
        is_active = (last_trade_date >= today) or is_consecutive(last_trade_date, today)
        
        # Find if the last compiled streak contains the last trade date
        last_streak = streaks[-1]
        if is_active and last_trade_date in last_streak:
            current_streak = len(last_streak)
            
    return current_streak, longest_streak


@trade.route("/trades/add", methods=["GET", "POST"])
@login_required
def add_trade():

    if request.method == "POST":

        trade_date_str = request.form.get("trade_date")
        trade_time_str = request.form.get("trade_time")
        amount_str = request.form.get("amount")
        discipline = request.form.get("discipline")
        notes = request.form.get("notes")

        # Required field validation
        if not trade_date_str or not amount_str or not discipline:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("trade.add_trade"))

        try:

            trade_date = datetime.strptime(
                trade_date_str,
                "%Y-%m-%d"
            ).date()

            # Weekend validation
            if trade_date.weekday() >= 5:
                flash(
                    "Trades cannot be logged on weekends.",
                    "danger"
                )
                return redirect(url_for("trade.add_trade"))

            trade_time = (
                datetime.strptime(
                    trade_time_str,
                    "%H:%M"
                ).time()
                if trade_time_str else None
            )

            amount = float(amount_str)

            if amount == 0:
                flash("Amount cannot be zero.", "danger")
                return redirect(url_for("trade.add_trade"))

            # Automatically determine profit/loss
            is_profit = amount > 0

            # Determine if plan was followed
            followed_plan = discipline == "yes"

            new_trade = Trade(
                user_id=current_user.id,
                trade_date=trade_date,
                trade_time=trade_time,
                amount=amount,
                is_profit=is_profit,
                followed_plan=followed_plan,
                notes=notes
            )

            db.session.add(new_trade)
            db.session.commit()

            flash("Trade logged successfully!", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error logging trade: {e}", "danger")
            return redirect(url_for("trade.add_trade"))

    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M")

    return render_template(
        "add_trade.html",
        today_str=today_str,
        now_str=now_str
    )

@trade.route("/trades/edit/<int:trade_id>", methods=["GET","POST"])
@login_required
def edit_trade(trade_id):

    trade=Trade.query.filter_by(
        id=trade_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        trade.trade_date = datetime.strptime(
            request.form.get("trade_date"),
            "%Y-%m-%d"
        ).date()

        if trade.trade_date.weekday() >= 5:
            flash(
                "Trades cannot be edited to weekends.",
                "danger"
            )
            return redirect(url_for("trade.edit_trade", trade_id=trade_id))

        trade.trade_date=trade.trade_date

        trade_time = request.form.get("trade_time")

        trade.trade_item =(
            datetime.strptime(
                trade_time,
                "%H:%M"
            ).time()
            if trade_time else None
        )

        trade.amount=float(
            request.form.get("amount")
        )

        trade.is_profit = trade.amount>0

        trade.followed_plan = (
            request.form.get("discipline") == "yes"
        )

        trade.notes = request.form.get("notes")

        db.session.commit()

        flash("Traade updated successfully", "success")

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_trade.html",
        trade=trade
    )

@trade.route("/trades/delete/<int:trade_id>", methods=["POST"])
@login_required
def delete_trade(trade_id):

    trade_item = Trade.query.filter_by(
        id=trade_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        db.session.delete(trade_item)
        db.session.commit()

        flash("Trade deleted successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting trade: {str(e)}", "danger")

    return redirect(url_for("dashboard"))