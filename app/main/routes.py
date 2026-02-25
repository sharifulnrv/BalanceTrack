from flask import Blueprint, render_template, send_file, Response
from app import db
from app.models import Account, Transaction, Category, Loan, Investment, Currency
from app.main.utils import export_transactions_to_excel, export_transactions_to_csv
from sqlalchemy import func
from datetime import datetime
from seed_data import seed_currencies, seed_categories

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Ensure default data exists
    seed_currencies()
    seed_categories()
    
    from app.models import Profile
    current_profile = Profile.query.filter_by(is_active=True).first()
    if not current_profile:
        return redirect(url_for('profiles.index'))

    # Calculate Net Worth
    total_balance = db.session.query(func.sum(Account.balance)).filter(Account.profile_id == current_profile.id).scalar() or 0
    investment_value = db.session.query(func.sum(Investment.current_value)).filter(Investment.profile_id == current_profile.id).scalar() or 0
    total_net_worth = total_balance + investment_value

    # Recent Transactions (Filter by accounts belonging to this profile)
    recent_transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.profile_id == current_profile.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate Monthly Metrics
    now = datetime.now()
    month = now.month
    year = now.year
    
    monthly_income = db.session.query(func.sum(Transaction.amount))\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.profile_id == current_profile.id)\
        .filter(Transaction.transaction_type == 'Income')\
        .filter(func.extract('month', Transaction.date) == month)\
        .filter(func.extract('year', Transaction.date) == year).scalar() or 0
        
    monthly_expense = db.session.query(func.sum(Transaction.amount))\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.profile_id == current_profile.id)\
        .filter(Transaction.transaction_type == 'Expense')\
        .filter(func.extract('month', Transaction.date) == month)\
        .filter(func.extract('year', Transaction.date) == year).scalar() or 0
        
    savings_rate = 0
    if monthly_income > 0:
        savings_rate = ((monthly_income - monthly_expense) / monthly_income) * 100
    
    # Accounts
    user_accounts = Account.query.filter_by(profile_id=current_profile.id).all()

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
            .filter(Account.profile_id == current_profile.id)\
            .filter(Transaction.transaction_type == 'Income')\
            .filter(func.extract('month', Transaction.date) == m)\
            .filter(func.extract('year', Transaction.date) == y).scalar() or 0
        income_data.append(float(inc))
        
        exp = db.session.query(func.sum(Transaction.amount))\
            .join(Account, Transaction.account_id == Account.id)\
            .filter(Account.profile_id == current_profile.id)\
            .filter(Transaction.transaction_type == 'Expense')\
            .filter(func.extract('month', Transaction.date) == m)\
            .filter(func.extract('year', Transaction.date) == y).scalar() or 0
        expense_data.append(float(exp))
        
    # Category Data for Donut Chart (Current Month)
    category_data = db.session.query(Category.name, func.sum(Transaction.amount))\
        .join(Transaction, Transaction.category_id == Category.id)\
        .join(Account, Transaction.account_id == Account.id)\
        .filter(Account.profile_id == current_profile.id)\
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
                           base_currency=Currency.query.filter_by(code='BDT').first())

@main.route('/export/excel')
def export_excel():
    output = export_transactions_to_excel()
    return send_file(output, 
                     download_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     as_attachment=True)

@main.route('/export/csv')
def export_csv():
    output = export_transactions_to_csv()
    return Response(output,
                    mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"})
