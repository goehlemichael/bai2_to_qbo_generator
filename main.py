import logging
import sys
import os
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog
import re
import csv
from datetime import datetime
import bai_processor

logging.basicConfig(stream=sys.stdout, level=logging.WARN, format='%(asctime)s - %(levelname)s - %(message)s')

user_set_input_dir = ""
user_set_output_dir = ""


def generate_csv_transaction_files(input_directory):
    input_files = input_directory
    output_csv_dir = tempfile.mkdtemp()

    files = os.listdir(input_files)

    sanitized_files = [file for file in files if re.match(r".*\.txt.*", file, re.IGNORECASE)]

    for file in sanitized_files:
        # Print the file name or perform any other operation
        file_path = os.path.join(input_directory, file)
        bai_processor.extract_bai_components(
            file_path,
            filename=file,
            filepath=output_csv_dir
        )
    return output_csv_dir


def generate_qbo_transaction_files():
    input_csv_dir = generate_csv_transaction_files(input_directory=user_set_input_dir)
    output_files = user_set_output_dir

    files = os.listdir(input_csv_dir)

    sanitized_csv_files = [file for file in files if re.match(r".+\.csv$", file, re.IGNORECASE)]

    for file in sanitized_csv_files:
        filename = file
        with open('{}/{}'.format(input_csv_dir, filename), 'r') as csvfile, \
                open('{}/{}.qbo'.format(output_files, filename), 'w') as ofxfile:
            reader = csv.DictReader(csvfile)
            ofxfile.write("OFXHEADER:100\n")
            ofxfile.write("DATA:OFXSGML\n")
            ofxfile.write("VERSION:102\n")
            ofxfile.write("SECURITY:NONE\n")
            ofxfile.write("ENCODING:USASCII\n")
            ofxfile.write("CHARSET:1252\n")
            ofxfile.write("COMPRESSION:NONE\n")
            ofxfile.write("OLDFILEUID:NONE\n")
            ofxfile.write("NEWFILEUID:NONE\n\n")

            ofxfile.write("<OFX>\n")
            ofxfile.write("<SIGNONMSGSRSV1>\n")
            ofxfile.write("<SONRS>\n")
            ofxfile.write("<STATUS>\n")
            ofxfile.write("<CODE>0\n")
            ofxfile.write("<SEVERITY>INFO\n")
            ofxfile.write("<MESSAGE>OK\n")
            ofxfile.write("</STATUS>\n")
            ofxfile.write("<DTSERVER>{0}.000[-4]\n".format(datetime.now().strftime("%Y%m%d%H%M%S")))
            ofxfile.write("<LANGUAGE>ENG\n")
            ofxfile.write("<INTU.BID>02102\n")
            ofxfile.write("</SONRS>\n")
            ofxfile.write("</SIGNONMSGSRSV1>\n")
            ofxfile.write("<BANKMSGSRSV1>\n")
            ofxfile.write("<STMTTRNRS>\n")
            ofxfile.write("<TRNUID>0\n")
            ofxfile.write("<STATUS>\n")
            ofxfile.write("<CODE>0\n")
            ofxfile.write("<SEVERITY>INFO\n")
            ofxfile.write("<MESSAGE>OK\n")
            ofxfile.write("</STATUS>\n")
            ofxfile.write("<STMTRS>\n")
            ofxfile.write("<CURDEF>USD\n")

            ofxfile.write("<BANKACCTFROM>\n")
            ofxfile.write("<BANKID>123456789\n")
            ofxfile.write("<ACCTID>9876543210\n")
            ofxfile.write("<ACCTTYPE>CHECKING\n")
            ofxfile.write("</BANKACCTFROM>\n")

            ofxfile.write("<BANKTRANLIST>\n")
            ofxfile.write("<DTSTART>{0}.000[-4]\n".format(datetime.now().strftime("%Y%m%d%H%M%S")))
            ofxfile.write("<DTEND>{0}.000[-4]\n".format(datetime.now().strftime("%Y%m%d%H%M%S")))

            for row in reader:
                date_string = row['Date']
                date = datetime.strptime(date_string, "%m/%d/%Y")
                formatted_date = date.strftime("%Y%m%d%H%M%S")

                ofxfile.write("<STMTTRN>\n")
                ofxfile.write("<TRNTYPE>{0}\n".format(row['Transaction'].upper()))
                ofxfile.write("<DTPOSTED>{0}.000[-4]\n".format(formatted_date))
                ofxfile.write("<TRNAMT>{0}\n".format(row['Amount']))
                ofxfile.write("<FITID>{0}\n".format(row['Bank Reference']))
                ofxfile.write("<NAME>{0}\n".format(row['Text'][:32]))
                ofxfile.write("<MEMO>{0}\n".format(row['Text'][-48:]))
                ofxfile.write("</STMTTRN>\n")

            ofxfile.write("</BANKTRANLIST>\n")

            ofxfile.write("<LEDGERBAL>\n")
            ofxfile.write("<BALAMT>0.00\n")
            ofxfile.write("<DTASOF>{0}.000[-4]\n".format(formatted_date))

            ofxfile.write("</LEDGERBAL>\n")
            ofxfile.write("</STMTRS>\n")
            ofxfile.write("</STMTTRNRS>\n")
            ofxfile.write("</BANKMSGSRSV1>\n")
            ofxfile.write("</OFX>\n")

    shutil.rmtree(input_csv_dir)


def select_input_directory():
    global user_set_input_dir
    user_set_input_dir = filedialog.askdirectory()
    input_dir_label.config(text=f"Input Directory: {user_set_input_dir}")
    enable_generate_button()


def select_output_directory():
    global user_set_output_dir
    user_set_output_dir = filedialog.askdirectory()
    output_dir_label.config(text=f"Output Directory: {user_set_output_dir}")
    enable_generate_button()


def enable_generate_button():
    if user_set_input_dir and user_set_output_dir:
        generate_button.config(state=tk.NORMAL)
    else:
        generate_button.config(state=tk.DISABLED)


try:
    window = tk.Tk()
    window.title('Convert to QBO')
    window.geometry('800x200')
    # Configure the window to accept file drops
    input_dir_button = tk.Button(window, text="Select Input Directory", command=select_input_directory)
    input_dir_button.pack()

    output_dir_button = tk.Button(window, text="Select Output Directory", command=select_output_directory)
    output_dir_button.pack()

    # Create labels to display the selected input and output directories
    input_dir_label = tk.Label(window, text="Input Directory: ")
    input_dir_label.pack()

    output_dir_label = tk.Label(window, text="Output Directory: ")
    output_dir_label.pack()

    # Create a button to trigger the file copy
    generate_button = tk.Button(window,
                                text="generate qbo files",
                                command=generate_qbo_transaction_files,
                                state=tk.DISABLED
                                )
    generate_button.pack()
    # Start the main event loop
    window.mainloop()
except Exception as e:
    logging.critical(f'something bad happened {e}')
