# this app does one main thing, translates a banks electronic statement(ebs) in a file that quickbooks can digest (qbo)
# bai2 formatted txt files inside input directory

# Docker
    docker build --tag baitoqbo .
    docker run -v <local_input>:/app/input_bank_data -v <local_output>:/app/output_qbo_txs --env BANKID=<routing number> --env ACCTID=<bank number> baitoqbo

# local run
    python3 -m venv venv
    pip install -r requirements.txt
    . venv/bin/activate
    python main.py
