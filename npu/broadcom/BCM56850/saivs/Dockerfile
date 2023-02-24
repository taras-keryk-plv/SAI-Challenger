FROM sc-base

MAINTAINER andriy.kokhan@gmail.com

ENV SC_PLATFORM=broadcom
ENV SC_ASIC=BCM56850
ENV SC_TARGET=saivs

WORKDIR /sai

# Install patch for SAI check
COPY patches/SAI/0001-improve-enum-values-integration-check-1727.patch /sai/

RUN git clone https://github.com/sonic-net/sonic-sairedis.git \
        && cd sonic-sairedis \
        && . /sai.env \
        && git checkout ${SAIREDIS_ID} \
        && git submodule update --init --recursive \
        && cd SAI && git fetch origin \
        && git checkout ${SAI_ID} \
        && git submodule update --init --recursive \
        && cd .. \
        && ./autogen.sh \
        && dpkg-buildpackage -us -uc -b --target=binary-syncd-vs --jobs=auto \
        && cd .. \
        && dpkg -i libsaivs_1.0.0_amd64.deb \
        && dpkg -i libsaivs-dev_1.0.0_amd64.deb \
        && dpkg -i libsairedis_1.0.0_amd64.deb \
        && dpkg -i libsairedis-dev_1.0.0_amd64.deb \
        && dpkg -i libsaimetadata_1.0.0_amd64.deb \
        && dpkg -i libsaimetadata-dev_1.0.0_amd64.deb \
        && dpkg -i syncd-vs_1.0.0_amd64.deb \
        && cp /sai/0001-improve-enum-values-integration-check-1727.patch /sai/sonic-sairedis \
        && cd sonic-sairedis && patch -p1 < 0001-improve-enum-values-integration-check-1727.patch \
        && cd SAI && make saithrift-install \
        && cp meta/saimetadatautils.c /sai/gen_attr_list/ \
        && cp meta/saimetadata.c /sai/gen_attr_list/ \
        && cp meta/saiserialize.c /sai/gen_attr_list/ \
        && mv /sai/sonic-sairedis/tests /sai/ \
        && rm -rf /sai/sonic-sairedis/* \
        && mv /sai/tests /sai/sonic-sairedis/

# Build SAI attributes metadata JSON generator and generate /etc/sai/sai.json
RUN cd /sai/gen_attr_list \
        && mkdir build && cd build \
        && cmake .. \
        && make -j$(nproc) \
        && mkdir -p /etc/sai \
        && ./attr_list_generator > /etc/sai/sai.json

# Setup supervisord
COPY configs/sai.profile       /etc/sai.d/sai.profile
COPY configs/lanemap.ini       /usr/share/sonic/hwsku/lanemap.ini
COPY configs/supervisord.conf  /etc/supervisor/conf.d/supervisord.conf

WORKDIR /sai-challenger/tests

CMD ["/usr/bin/supervisord"]

