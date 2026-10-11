
import math
from datetime import datetime, date, time, timedelta

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from extensions import db
from models.trade import Trade


trade = Blueprint("trade", __name__)


def is_consecutive(d1, d2):
    """Return whether two dates are consecutive trading days,
    treating Friday-to-Monday as consecutive.
    """
    if d1 > d2:
        d1, d2 = d2, d1

    diff = (d2 - d1).days

    if diff <= 1:
        return True

    if d1.weekday() == 4 and d2.weekday() == 0 and diff <= 3:
        return True

    if d1.weekday() in (5, 6) and d2.weekday() == 0 and diff <= 2:
        return True

    return False


def calculate_streaks(trades):
    """Calculate current and longest streaks of disciplined trading days.
    A day is disciplined only when every trade that day followed the plan.
    """
    if not trades:
        return 0, 0

    daily_status = {}

    for trade_item in trades:
        trade_date = trade_item.trade_date

        if trade_date not in daily_status:
            daily_status[trade_date] = True

        if trade_item.followed_plan is False:
            daily_status[trade_date] = False

    sorted_dates = sorted(daily_status.keys())

    streaks = []
    current_streak_dates = []

    for trade_date in sorted_dates:
        if daily_status[trade_date]:
            if not current_streak_dates:
                current_streak_dates.append(trade_date)
            else:
                last_date = current_streak_dates[-1]

                if is_consecutive(last_date, trade_date):
                    current_streak_dates.append(trade_date)
                else:
                    streaks.append(current_streak_dates)
                    current_streak_dates = [trade_date]
        else:
            if current_streak_dates:
                streaks.append(current_streak_dates)
                current_streak_dates = []

    if current_streak_dates:
        streaks.append(current_streak_dates)

    longest_streak = max((len(streak) for streak in streaks), default=0)

    current_streak = 0
    last_trade_date = sorted_dates[-1]
    today = date.today()

    # Do not allow a future-dated trade to activate the current streak.
    is_active = (
        last_trade_date <= today
        and is_consecutive(last_trade_date, today)
    )

    if streaks and is_active and last_trade_date in streaks[-1]:
        current_streak = len(streaks[-1])

    return current_streak, longest_streak


def parse_trade_form():
    """Validate and parse submitted trade form fields."""
    trade_date_str = request.form.get("trade_date", "").strip()
    trade_time_str = request.form.get("trade_time", "").strip()
    amount_str = request.form.get("amount", "").strip()
    discipline = request.form.get("discipline", "").strip()

    if not trade_date_str or not amount_str or discipline not in ("yes", "no"):
        raise ValueError("Please fill in all required fields.")

    trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()

    if trade_date.weekday() >= 5:
        raise ValueError("Trades cannot be logged on weekends.")

    trade_time = (
        datetime.strptime(trade_time_str, "%H:%M").time()
        if trade_time_str
        else None
    )

    amount = float(amount_str)

    if not math.isfinite(amount) or amount == 0:
        raise ValueError("Amount must be a valid, non-zero number.")

    return {
        "trade_date": trade_date,
        "trade_time": trade_time,
        "amount": amount,
        "is_profit": amount > 0,
        "followed_plan": discipline == "yes",
        "notes": request.form.get("notes", "").strip() or None,
    }


@trade.route("/trades/add", methods=["GET", "POST"])
@login_required
def add_trade():
    if request.method == "POST":
        try:
            values = parse_trade_form()

            new_trade = Trade(
                user_id=current_user.id,
                **values
            )

            db.session.add(new_trade)
            db.session.commit()

            flash("Trade logged successfully!", "success")
            return redirect(url_for("dashboard"))

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
            return redirect(url_for("trade.add_trade"))

        except Exception:
            db.session.rollback()
            flash("Unable to log the trade. Please try again.", "danger")
            return redirect(url_for("trade.add_trade"))

    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M")

    return render_template(
        "add_trade.html",
        today_str=today_str,
        now_str=now_str
    )


@trade.route("/trades/edit/<int:trade_id>", methods=["GET", "POST"])
@login_required
def edit_trade(trade_id):
    trade_item = Trade.query.filter_by(
        id=trade_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        try:
            values = parse_trade_form()

            trade_item.trade_date = values["trade_date"]
            trade_item.trade_time = values["trade_time"]
            trade_item.amount = values["amount"]
            trade_item.is_profit = values["is_profit"]
            trade_item.followed_plan = values["followed_plan"]
            trade_item.notes = values["notes"]

            db.session.commit()

            flash("Trade updated successfully.", "success")
            return redirect(url_for("dashboard"))

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
            return redirect(url_for("trade.edit_trade", trade_id=trade_id))

        except Exception:
            db.session.rollback()
            flash("Unable to update the trade. Please try again.", "danger")
            return redirect(url_for("trade.edit_trade", trade_id=trade_id))

    return render_template(
        "edit_trade.html",
        trade=trade_item
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

    except Exception:
        db.session.rollback()
        flash("Unable to delete the trade. Please try again.", "danger")

    return redirect(url_for("dashboard"))