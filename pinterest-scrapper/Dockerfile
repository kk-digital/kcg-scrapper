FROM ubuntu:22.04

ARG root_password

# Setup SSH
RUN apt-get update || echo "OK" && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo "root:${root_password}" | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN apt install -y git
RUN apt install -y nano
RUN apt install -y wget
RUN apt install -y curl
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -yqq fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libu2f-udev libvulkan1 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils
RUN dpkg -i google-chrome-stable_current_amd64.deb

# Clone repo
WORKDIR /
RUN git clone https://github.com/kk-digital/kcg-scrapper && mv kcg-scrapper/pinterest-scrapper /pinterest-scrapper
WORKDIR /pinterest-scrapper

# Add etc/profile
#COPY profile /etc/profile
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
RUN apt install -y python3.10-venv
RUN pip3 install --no-cache -r requirements.txt

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]