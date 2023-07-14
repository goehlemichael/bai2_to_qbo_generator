FROM python:3.7-alpine3.17
ENV BANKID $BANKID
ENV ACCTID $ACCTID
RUN apk add --no-cache tzdata
ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN mkdir input_bank_data output_qbo_txs output_csv_txs
COPY requirements.txt thinkbai2.py thinkbrq_bai_processor.py /app/
RUN pip3 install -r requirements.txt
# This line is for testing. It executes the program once every minute
RUN echo "* * * * * python /app/main.py >> /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontabs/root
# the arrival is random between the hours of 7 am and 10 am
#RUN echo "00 11 * * * python /app/main.py >> /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontabs/root
CMD ["crond", "-f"]
