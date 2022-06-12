# Dockerfile

FROM ubuntu:latest

# Define work directory
WORKDIR /workplace

# Install Python for script execution
# Install Cron & systemctl for automate
RUN apt-get update \
    && apt-get install -y python3-pip \
    && apt-get install -y cron

ADD requirements.txt /workplace
RUN pip3 install -r /workplace/requirements.txt

# Setup environment variables for the conmtainer
ARG SCRIPT_PATH=/workplace/scripts
ARG ETC_PATH=/workplace/etc
ARG DATA_PATH=/workplace/data

# Export environment variable to the container
ENV SCRIPT_PATH=${SCRIPT_PATH}
ENV ETC_PATH=${ETC_PATH}
ENV DATA_PATH=${DATA_PATH}

# Setting up cron
ADD cron_job /workplace
RUN printenv | grep "SCRIPT_PATH" >> /etc/environment
RUN printenv | grep "ETC_PATH" >> /etc/environment
RUN printenv | grep "DATA_PATH" >> /etc/environment
RUN crontab /workplace/cron_job

# Setting up script
RUN mkdir -p ${SCRIPT_PATH}
COPY scripts ${SCRIPT_PATH}
RUN chmod +x ${SCRIPT_PATH}/*.py

CMD ["cron", "-f"]
