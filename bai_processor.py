import sys
import csv
from bai2 import bai2
import logging
from tkinter import messagebox

logging.basicConfig(stream=sys.stdout, level=logging.WARN, format='%(asctime)s - %(levelname)s - %(message)s')


def process_account_summary(summary):
    summary_data = {
        'BAI Code': summary.type_code.code,
        'Level': summary.type_code.level.value,
        'Description': summary.type_code.description,
        'Amount': summary.amount,
        'Count': summary.item_count,
        'Fund Type': summary.funds_type,
        'Availability': summary.availability
    }
    logging.debug(f"summary data: {summary_data}")
    return summary_data


def process_account_header(header):
    summary_list = []
    summary_items = header.summary_items
    for account_summary in summary_items:
        summary_data = process_account_summary(account_summary)
        summary_list.append(summary_data)
    logging.debug(f"summary list: {summary_list}")
    return summary_list


def process_account_transactions(identifier, transactions):
    list_transactions = []
    # TransactionDetail
    for transaction in transactions:
        transaction_dict = {
            'Customer Account Number': identifier.customer_account_number,
            'Currency': identifier.currency,
            'BAI Code': transaction.type_code.code,
            'Transaction': transaction.type_code.transaction.value,
            'Level': transaction.type_code.level.detail.value,
            'Description': transaction.type_code.description,
            'Amount': transaction.amount,
            'Fund Type': transaction.funds_type,
            'Availability': transaction.availability,
            'Bank Reference': transaction.bank_reference,
            'Customer Reference': transaction.customer_reference,
            'Text': transaction.text
        }
        list_transactions.append(transaction_dict)
    logging.debug(f"list transactions: {list_transactions}")
    return list_transactions


def process_accounts(accounts):
    list_transactions = []
    summary_accounts = []
    for account in accounts:
        account_identifier = account.header
        account_trailer = account.trailer
        account_transactions = account.children
        # Process Entities
        summary_list = process_account_header(account_identifier)
        tr_list = process_account_transactions(account_identifier, account_transactions)
        list_transactions = list_transactions + tr_list
        summary_accounts = summary_accounts + summary_list
    logging.debug(f"Process Accounts: list transactions - {list_transactions} summary accounts - {summary_accounts}")
    return list_transactions, summary_accounts


def process_bai_header(bai_header):
    header_dict = {
        'Sender ID': bai_header.sender_id,
        'Receiver ID': bai_header.receiver_id,
        'Creation Date': bai_header.creation_date.strftime(
            '%m/%d/%Y') if bai_header.creation_date is not None else None,
        'Creation Time': bai_header.creation_time.strftime('%H:%M') if bai_header.creation_time is not None else None,
        'File ID': bai_header.file_id,
    }
    logging.debug(f"process bai header: {header_dict}")
    return header_dict


def process_bai_grp_header(grp_header):
    grp_dict_head = {
        'Ultimate Receiver ID': grp_header.ultimate_receiver_id,
        'Originator ID': grp_header.originator_id,
        'Group Status': grp_header.group_status.name if grp_header.group_status is not None else None,
        'As of date': grp_header.as_of_date.strftime('%m/%d/%Y') if grp_header.as_of_date is not None else None,
        'As of time': grp_header.as_of_time.strftime('%H:%M') if grp_header.as_of_time is not None else None,
        'Currency': grp_header.currency,
        'As of Date Modifier': grp_header.as_of_date_modifier.name if grp_header.as_of_date_modifier is not None else None,

    }
    logging.debug(f"process bai grp header: {grp_dict_head}")
    return grp_dict_head


def process_file_data(file_data):
    # Extract Header, Trailer, Transaction Data
    bai_file_header = file_data.header
    bai_file_trailer = file_data.trailer
    header_dict = process_bai_header(bai_file_header)
    # File Group
    bai_file_group = file_data.children[0]
    bai_file_grp_header = bai_file_group.header
    bai_file_grp_trailer = bai_file_group.trailer
    grp_header_dict = process_bai_grp_header(bai_file_grp_header)
    # Accounts
    accounts = bai_file_group.children
    list_transactions, summary_accounts = process_accounts(accounts)
    logging.debug(f"process file data:"
                  f"header dict - {header_dict}"
                  f"grp header dict - {grp_header_dict}"
                  f"list transactions {list_transactions}"
                  f"summary accounts {summary_accounts}"
                  )
    return header_dict, grp_header_dict, list_transactions, summary_accounts


def parse_from_file(f, **kwargs):
    try:
        with open(f, 'r', encoding='utf-8') as bai_file:
            lines = bai_file.readlines()
            proc_lines = []
            for line in lines:
                # cleanup lines and remove whitespaces
                pr_line = line.strip()
                proc_lines.append(pr_line)
            logging.debug(f"data parsed from file{proc_lines}")
            return bai2.parse_from_lines(proc_lines, **kwargs)
    except UnicodeDecodeError:
        logging.warning(f"Invalid UTF-8 encoding in file: {f}")


def extract_bai_components(f, filename='', filepath='.', **kwargs):
    file_data = parse_from_file(f, **kwargs)
    header_dict, grp_header_dict, list_transactions, summary_accounts = process_file_data(file_data)
    date = grp_header_dict['As of date']
    time = grp_header_dict['As of time']
    logging.debug(f"header dict - {header_dict},"
                  f"grp header dict - {grp_header_dict},"
                  f"list transactions - {list_transactions},"
                  f"summary accounts - {summary_accounts},"
                  f"date - {date},"
                  f"time - {time},"
                  f"**kwargs"
                  )

    create_csv_file(filename,
                    filepath,
                    date=date,
                    transactions=list_transactions,
                    summary=summary_accounts,
                    **kwargs
                    )

    return header_dict, grp_header_dict, list_transactions, summary_accounts


def create_csv_file(filename, filepath, date, transactions, summary, **kwargs):
    if not transactions:
        logging.warning(f"no transactions {filename}")
        messagebox.showinfo("Alert", f"no transactions {filename}")
        return
    for transaction in transactions:
        # append date column to the object
        transaction['Date'] = date
        # include decimal in the amount value
        no_decimal = transaction['Amount']
        yes_decimal = str(no_decimal)[:-2] + "." + str(no_decimal)[-2:]
        transaction['Amount'] = yes_decimal
        # append a negative sign to credit type transactions
        if transaction['Transaction'] == 'debit':
            transaction['Amount'] = "-" + transaction['Amount']

    if len(transactions) > 0:
        with open('{}/transactions-{}.csv'.format(filepath,
                                                  filename
                                                  ),
                  'w', encoding='utf8', newline='') as output_file:
            fieldnames = ['Date', 'Description', 'Amount', 'Customer Account Number', 'Currency', 'BAI Code',
                          'Transaction', 'Level', 'Fund Type', 'Availability', 'Bank Reference', 'Customer Reference',
                          'Text']
            dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            dict_writer.writeheader()
            dict_writer.writerows(transactions)
