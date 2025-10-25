# --- Base Image ---
# Use an official Python runtime as a parent image.
# 'slim' is a good choice for smaller image size.
FROM python:3.11-slim

# --- Environment Variables ---
# Prevents Python from writing .pyc files to disc.
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures that Python output is sent straight to the terminal without buffering.
ENV PYTHONUNBUFFERED 1

# --- Create a non-root user ---
# [NEW] Create a dedicated group and user to run the application
RUN addgroup --system app && adduser --system --group app

# --- Application Directory & Permissions ---
# Set the working directory in the container.
WORKDIR /app
# [NEW] Set ownership of the app directory to the new user
RUN chown app:app /app

# --- Install Dependencies ---
# Copy the requirements file into the container.
COPY requirements.txt .
# Install the dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# --- Switch to the non-root user ---
# [NEW] From now on, all subsequent commands will run as 'appuser'
USER app

# --- Copy Application Code ---
# Copy the rest of the application's code into the container.
COPY . .

# --- Expose Port ---
# Expose the port Gunicorn will run on.
EXPOSE 8000

# --- Collect Static Files ---
# This will be run when the image is built.
# NOTE: This command is now run by the 'app' user.
# Ensure 'staticfiles' directory is writable by this user if it's created manually.
# Django's collectstatic creates the directory itself, so this should be fine.
RUN python manage.py collectstatic --noinput

# --- Command to Run ---
# Run Gunicorn.
# The number of workers is a good starting point. Adjust based on your server's CPU cores.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "core.wsgi:application"]