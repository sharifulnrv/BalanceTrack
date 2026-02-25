from app import create_app, db
from app.models import Category, Currency

def seed_categories():
    if Category.query.first():
        return
        
    categories = [
        # Expenses
        {'name': 'Food & Drinks', 'icon': 'ph-hamburger', 'is_income': False},
        {'name': 'Shopping', 'icon': 'ph-shopping-bag', 'is_income': False},
        {'name': 'Housing', 'icon': 'ph-house-line', 'is_income': False},
        {'name': 'Transportation', 'icon': 'ph-car', 'is_income': False},
        {'name': 'Utilities', 'icon': 'ph-lightbulb', 'is_income': False},
        {'name': 'Entertainment', 'icon': 'ph-ticket', 'is_income': False},
        {'name': 'Health', 'icon': 'ph-first-aid', 'is_income': False},
        # Income
        {'name': 'Salary', 'icon': 'ph-money', 'is_income': True},
        {'name': 'Business', 'icon': 'ph-briefcase', 'is_income': True},
        {'name': 'Gifts', 'icon': 'ph-gift', 'is_income': True},
        {'name': 'Investment Return', 'icon': 'ph-chart-line-up', 'is_income': True},
    ]
    
    for cat_data in categories:
        cat = Category(**cat_data)
        db.session.add(cat)
    db.session.commit()

def seed_currencies():
    if Currency.query.first():
        return
    
    currencies = [
        {'code': 'USD', 'symbol': '$', 'exchange_rate': 1.0},
        {'code': 'BDT', 'symbol': '৳', 'exchange_rate': 120.0},
        {'code': 'EUR', 'symbol': '€', 'exchange_rate': 0.92},
        {'code': 'GBP', 'symbol': '£', 'exchange_rate': 0.79},
    ]
    
    for curr_data in currencies:
        curr = Currency(**curr_data)
        db.session.add(curr)
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # This is just a utility function, normally called after registration
        print("Category seeding utility ready.")
