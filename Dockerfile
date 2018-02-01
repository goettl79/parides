FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd -r parides && useradd --no-log-init -r -g parides parides
COPY . .
ENTRYPOINT [ "python3", "-m" , "parides.cli" ]
USER parides