FROM python:3.11.3

ARG root_password

RUN apt update && apt upgrade -y
RUN apt install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo "root:${root_password}" | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -f -y ./google-chrome-stable_current_amd64.deb

RUN git clone https://github.com/kk-digital/kcg-scrapper
WORKDIR kcg-scrapper/pinterest-scrapper/

RUN pip install --no-cache -r requirements.txt

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
