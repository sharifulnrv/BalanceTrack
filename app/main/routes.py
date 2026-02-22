from flask import Blueprint, render_template, send_file, Response
from flask_login import login_required, current_user
from app import db
from app.models import Account, Transaction, Category, Loan, Investment, Currency
from app.main.utils import export_transactions_to_excel, export_transactions_to_csv
from sqlalchemy import func
from datetime import datetime
from seed_data import seed_currencies

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    # Ensure default currencies exist
    seed_currencies()
    
    # Calculate Net Worth
    total_balance = db.session.query(func.sum(Account.balance)).filter(Account.user_id == current_user.id).scalar() or 0
    investment_value = db.session.query(func.sum(Investment.current_value)).filter(Investment.user_id == current_user.id).scalar() or 0
    total_net_worth = total_balance + investment_value

    # Recent Transactions
    recent_transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.user_id == current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate Monthly Metrics
    now = datetime.now()
    month = now.month
    year = now.year
    
    monthly_income = db.session.query(func.sum(Transaction.amount))\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.user_id == current_user.id)\
        .filter(Transaction.transaction_type == 'Income')\
        .filter(func.extract('month', Transaction.date) == month)\
        .filter(func.extract('year', Transaction.date) == year).scalar() or 0
        
    monthly_expense = db.session.query(func.sum(Transaction.amount))\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.user_id == current_user.id)\
        .filter(Transaction.transaction_type == 'Expense')\
        .filter(func.extract('month', Transaction.date) == month)\
        .filter(func.extract('year', Transaction.date) == year).scalar() or 0
        
    savings_rate = 0
    if monthly_income > 0:
        savings_rate = ((monthly_income - monthly_expense) / monthly_income) * 100
    
    # Accounts
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()

    # Calculate Chart Data (Last 6 Months)
    from datetime import timedelta
    chart_months = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
        first_of_month = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        m = first_of_month.month
        y = first_of_month.year
        chart_months.append(first_of_month.strftime('%b'))
        
        inc = db.session.query(func.sum(Transaction.amount))\
            .join(Account, Transaction.account_id == Account.id)\
            .filter(Account.user_id == current_user.id)\
            .filter(Transaction.transaction_type == 'Income')\
            .filter(func.extract('month', Transaction.date) == m)\
            .filter(func.extract('year', Transaction.date) == y).scalar() or 0
        income_data.append(float(inc))
        
        exp = db.session.query(func.sum(Transaction.amount))\
            .join(Account, Transaction.account_id == Account.id)\
            .filter(Account.user_id == current_user.id)\
            .filter(Transaction.transaction_type == 'Expense')\
            .filter(func.extract('month', Transaction.date) == m)\
            .filter(func.extract('year', Transaction.date) == y).scalar() or 0
        expense_data.append(float(exp))
        
    # Category Data for Donut Chart (Current Month)
    category_data = db.session.query(Category.name, func.sum(Transaction.amount))\
        .join(Transaction, Transaction.category_id == Category.id)\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.user_id == current_user.id)\
        .filter(Transaction.transaction_type == 'Expense')\
        .filter(func.extract('month', Transaction.date) == month)\
        .filter(func.extract('year', Transaction.date) == year)\
        .group_by(Category.name).all()
        
    category_labels = [row[0] for row in category_data]
    category_values = [float(row[1]) for row in category_data]

    return render_template('index.html', 
                           net_worth=total_net_worth,
                           transactions=recent_transactions,
                           accounts=user_accounts,
                           monthly_income=monthly_income,
                           monthly_expense=monthly_expense,
                           savings_rate=savings_rate,
                           chart_months=chart_months,
                           income_data=income_data,
                           expense_data=expense_data,
                           category_labels=category_labels,
                           category_values=category_values,
                           base_currency=current_user.base_currency or Currency.query.filter_by(code='BDT').first())

@main.route('/export/excel')
@login_required
def export_excel():
    output = export_transactions_to_excel(current_user.id)
    return send_file(output, 
                     download_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     as_attachment=True)

@main.route('/export/csv')
@login_required
def export_csv():
    output = export_transactions_to_csv(current_user.id)
    return Response(output,
                    mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"})
