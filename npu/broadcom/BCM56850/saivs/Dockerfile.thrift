FROM sc-thrift-base

MAINTAINER andriy.kokhan@gmail.com

# Setup supervisord
COPY configs/sai.profile       /etc/sai.d/sai.profile
COPY configs/lanemap.ini       /usr/share/sonic/hwsku/lanemap.ini
COPY configs/supervisord.conf  /etc/supervisor/conf.d/supervisord.conf
COPY configs/port_config.ini             /usr/share/sonic/hwsku/port_config.ini
COPY configs/supervisord.conf.saithrift  /etc/supervisor/conf.d/supervisord.conf

WORKDIR /sai-challenger/tests

CMD ["/usr/bin/supervisord"]

