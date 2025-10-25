# --- Stage 1: Build Stage ---
# Use a temporary image to install dependencies.
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install build-time dependencies if any (e.g., for compiling C extensions)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# --- Stage 2: Final Production Image ---
# Start from a clean, slim base image again.
FROM python:3.11-slim

# Create a non-root user to run the application for security
RUN addgroup --system app && adduser --system --group app

# Set the working directory
WORKDIR /app

# Copy the installed Python packages from the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy the application code into the container
# This will be efficient because of the .dockerignore file
COPY . .

# Set ownership of the application directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app will run on
EXPOSE 8000

# The CMD is now much simpler.
# We let the hosting platform (like Darkube) handle collectstatic and migrations.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "core.wsgi:application"]