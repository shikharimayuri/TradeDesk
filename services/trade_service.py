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

@trade.route("/dashboard")
@login_required
def dashboard():
    # Fetch all user trades ordered by date ascending, then time ascending
    user_trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date.asc(), Trade.trade_time.asc()).all()
    
    # Streaks
    current_streak, longest_streak = calculate_streaks(user_trades)
    
    # Win rate (accuracy) on last 10 trades
    # For win rate, we want the 10 most recent trades in chronological order
    last_10_trades = user_trades[-10:]
    win_rate = 0.0
    if last_10_trades:
        wins = sum(1 for t in last_10_trades if t.is_profit)
        win_rate = round((wins / len(last_10_trades)) * 100, 1)
        
    # Net Profit / Loss
    net_profit = 0.0
    for t in user_trades:
        amount = float(t.amount) if t.amount else 0.0
        if t.is_profit:
            net_profit += amount
        else:
            net_profit -= amount
    net_profit = round(net_profit, 2)
    
    # Weekly Analytics (last 7 days net profit/loss)
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    daily_net = {d: 0.0 for d in last_7_days}
    for t in user_trades:
        if t.trade_date in daily_net:
            amount = float(t.amount) if t.amount else 0.0
            if t.is_profit:
                daily_net[t.trade_date] += amount
            else:
                daily_net[t.trade_date] -= amount
                
    chart_labels = [d.strftime("%a (%b %d)") for d in last_7_days]
    chart_values = [round(daily_net[d], 2) for d in last_7_days]
    
    # Render trades list in reverse chronological order for recent display
    recent_trades = sorted(user_trades, key=lambda x: (x.trade_date, x.trade_time or time(0,0)), reverse=True)
    
    return render_template(
        "dashboard.html",
        current_streak=current_streak,
        longest_streak=longest_streak,
        win_rate=win_rate,
        net_profit=net_profit,
        chart_labels=chart_labels,
        chart_values=chart_values,
        recent_trades=recent_trades
    )

@trade.route("/trades/add", methods=["GET", "POST"])
@login_required
def add_trade():
    if request.method == "POST":
        trade_date_str = request.form.get("trade_date")
        trade_time_str = request.form.get("trade_time")
        amount_str = request.form.get("amount")
        outcome = request.form.get("outcome") # "profit" or "loss"
        discipline = request.form.get("discipline") # "yes" or "no"
        notes = request.form.get("notes")
        
        # Validations
        if not trade_date_str or not amount_str or not outcome or not discipline:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("trade.add_trade"))
            
        try:
            trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
            trade_time = datetime.strptime(trade_time_str, "%H:%M").time() if trade_time_str else None
            amount = float(amount_str)
            is_profit = True if outcome == "profit" else False
            followed_plan = True if discipline == "yes" else False
            
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
            return redirect(url_for("trade.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error logging trade: {str(e)}", "danger")
            return redirect(url_for("trade.add_trade"))
            
    # Default values for GET request
    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M")
    return render_template("add_trade.html", today_str=today_str, now_str=now_str)

@trade.route("/trades/delete/<int:trade_id>", methods=["POST"])
@login_required
def delete_trade(trade_id):
    trade_item = Trade.query.get_or_404(trade_id)
    if trade_item.user_id != current_user.id:
        flash("You are not authorized to delete this trade.", "danger")
        return redirect(url_for("trade.dashboard"))
        
    try:
        db.session.delete(trade_item)
        db.session.commit()
        flash("Trade deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting trade: {str(e)}", "danger")
        
    return redirect(url_for("trade.dashboard"))