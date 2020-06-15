FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd -r parides && useradd --no-log-init -r -g parides parides
COPY . .
RUN python setup.py build
RUN python setup.py install
ENTRYPOINT [ "parides" ]
