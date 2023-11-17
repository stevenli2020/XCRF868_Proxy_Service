FROM ubuntu:20.04
MAINTAINER steven
ENV OS_LOCALE="en_US.UTF-8"
RUN apt-get update && apt-get install -y python3 python3-requests python3-websocket python3-typing-extensions python3-tornado nano openssh-server curl
RUN apt-get autoremove
RUN mkdir /app
COPY ./entrypoint.sh /sbin/entrypoint.sh
RUN sed -i -e 's/\r$//' /sbin/entrypoint.sh
RUN chmod 755 /sbin/entrypoint.sh
EXPOSE 22
WORKDIR /app
