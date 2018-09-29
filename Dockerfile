FROM python:3.6

# Download requirements
COPY requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

# Download spacy model
RUN python -m spacy download en
