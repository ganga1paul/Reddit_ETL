# Use Airflow base image with Python 3.10
FROM apache/airflow:2.7.2-python3.10

# Switch to root to install system dependencies
USER root

# Install additional dependencies like pip, and libpq-dev
RUN apt-get update && apt-get install -y \
    python3-pip \
    libpq-dev 
RUN apt-get update && apt-get install -y openjdk-11-jre
# Switch back to the airflow user to avoid running pip as root
USER airflow
RUN pip install --upgrade pip



# Install Python dependencies for your project
COPY requirements.txt .
RUN pip install -r requirements.txt



# Expose the port the Airflow webserver runs on
EXPOSE 8080

# Command to run Airflow, initializes DB, and starts webserver and scheduler
CMD ["bash", "-c", "airflow db init && airflow webserver & airflow scheduler"]
