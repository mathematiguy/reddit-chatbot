FROM docker.dragonfly.co.nz/dragonverse-18.04

# Install python3.6
RUN apt install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa && \
	apt-get update && \
	apt-get install -y python3.6 python3-pip

# Download requirements
COPY requirements.txt /root/requirements.txt
RUN pip3 install -r /root/requirements.txt

# Download spacy model
RUN python3 -m spacy download en
