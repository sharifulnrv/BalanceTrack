import pandas as pd
from io import BytesIO
from app.models import Transaction, Account

def export_transactions_to_excel(user_id):
    transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.user_id == user_id).all()
    
    data = []
    for tx in transactions:
        data.append({
            'Date': tx.date.strftime('%Y-%m-%d'),
            'Account': tx.account.name,
            'Type': tx.transaction_type,
            'Category': tx.category.name if tx.category else 'Uncategorized',
            'Amount': tx.amount,
            'Description': tx.description
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
    
    output.seek(0)
    return output

def export_transactions_to_csv(user_id):
    transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.user_id == user_id).all()
    
    data = []
    for tx in transactions:
        data.append({
            'Date': tx.date.strftime('%Y-%m-%d'),
            'Account': tx.account.name,
            'Type': tx.transaction_type,
            'Category': tx.category.name if tx.category else 'Uncategorized',
            'Amount': tx.amount,
            'Description': tx.description
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')
