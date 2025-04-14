FROM python:3.12-slim

# Install necessary dependencies
RUN apt update && apt install -y locales

# Set up the locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANGUAGE=en_US:en
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Set working directory
WORKDIR /src

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install Python dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and group
RUN groupadd -r moneroj && useradd --no-log-init -r -g moneroj moneroj

# Change ownership of the application files to the non-root user
# This ensures the user has proper access to files they will use later.
COPY --chown=moneroj:moneroj app/ app/

# Switch to the non-root user
USER moneroj:moneroj

# Set the working directory for app-related files
WORKDIR /src/app

# Run linting as the non-root user
RUN pylint \
    --rcfile="/src/app/.pylintrc" \
    /src/app

# Start the application using gunicorn (as the non-root user)
ENTRYPOINT ["gunicorn", "moneropro.wsgi:application"]
