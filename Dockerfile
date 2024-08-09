FROM openproject/openproject:14

RUN apt update \
    && apt install -y \
    python3-pip \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

RUN mv /usr/lib/python3.11/EXTERNALLY-MANAGED /usr/lib/python3.11/EXTERNALLY-MANAGED.old

COPY requirements.txt /
RUN python3 -m pip install -r /requirements.txt \
    && rm /requirements.txt

COPY ex_app/lib /ex_app/lib
COPY docker/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["bash"]
CMD ["/entrypoint.sh"]