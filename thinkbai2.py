import logging
import sys
import os
import re
import csv
from datetime import datetime
import thinkbrq_bai_processor

logging.basicConfig(stream=sys.stdout, level=logging.WARN, format='%(asctime)s - %(levelname)s - %(message)s')
bankid = os.environ['BANKID']
acctid = os.environ['ACCTID']


def generate_csv_transaction_files():
    # define directories for input_bank_data and output_csv_txs
    data_input_directory = "/app/input_bank_data"
    output_dir = "/app/output_csv_txs"
    logging.info(f'input directory is {data_input_directory}')
    logging.info(f"output directory is {output_dir}")

    # ensure input_bank_data directory exists
    if not os.path.exists(data_input_directory) or not os.path.isdir(data_input_directory):
        logging.critical(f"there is no {data_input_directory} directory")
        return

    files = os.listdir(data_input_directory)

    sanitized_files = [file for file in files if re.match(r".*\.txt.*", file, re.IGNORECASE)]

    for file in sanitized_files:
        # Print the file name or perform any other operation
        file_path = os.path.join(data_input_directory, file)
        thinkbrq_bai_processor.extract_bai_components(
            file_path,
            filename=file,
            filepath=output_dir
        )


def generate_qbo_transaction_files():
    # define directories for input_bank_data and output_csv_txs
    output_csv_generated = "/app/output_csv_txs"
    output_qbo_generated = "/app/output_qbo_txs"
    logging.info(f"input directory {output_csv_generated}")
    logging.info(f"output directory {output_qbo_generated}")

    # ensure output_qbo_txs directory exists
    if not os.path.exists(output_qbo_generated) or not os.path.isdir(output_qbo_generated):
        logging.critical(f"there is no {output_qbo_generated} directory")
        return

    files = os.listdir(output_csv_generated)

    sanitized_csv_files = [file for file in files if re.match(r".+\.csv$", file, re.IGNORECASE)]

    for file in sanitized_csv_files:
        filename = file
        with open('{}/{}'.format(output_csv_generated, filename), 'r') as csvfile, \
                open('{}/{}.qbo'.format(output_qbo_generated, filename), 'w') as ofxfile:
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

            # Write the OFX body
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
            ofxfile.write(f"<BANKID>{bankid}\n")
            ofxfile.write(f"<ACCTID>{acctid}\n")
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

            # Write the OFX footer
            ofxfile.write("</LEDGERBAL>\n")
            ofxfile.write("</STMTRS>\n")
            ofxfile.write("</STMTTRNRS>\n")
            ofxfile.write("</BANKMSGSRSV1>\n")
            ofxfile.write("</OFX>\n")


try:
    generate_csv_transaction_files()
    generate_qbo_transaction_files()
except Exception as e:
    logging.critical(f'something bad happened {e}')
