FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    telnet \
    && rm -rf /var/lib/apt/lists/*

COPY docker/python/requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv
RUN apt-get update && apt-get install -y expect

# install php 8.4 
RUN apt-get install -y php8.4-cli

RUN apt-get update && apt-get install -y socat && rm -rf /var/lib/apt/lists/*

RUN pip install flask --break-system-packages

RUN pip install pyodbc --break-system-packages

RUN pip install django-pyodbc-azure

# Update the package list and install curl and lsb-release
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl lsb-release && \
    # Add the Microsoft GPG key
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg && \
    # Add the Microsoft repository with the key
    echo "deb [signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    # Update the package list again
    apt-get update && \
    # Install the ODBC driver
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    # Clean up
    rm -rf /var/lib/apt/lists/*

CMD ["tail", "-f", "/dev/null"]
