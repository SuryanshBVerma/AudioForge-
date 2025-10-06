# Dockerfile (Corrected)

# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory for the application
WORKDIR /app

# 3. Install espeak and git, which are required
RUN apt-get update && apt-get install -y espeak git && rm -rf /var/lib/apt/lists/*

# 4. Clone the neutts-air repository
# We clone it into a subdirectory to keep things organized
WORKDIR /
RUN git clone https://github.com/neuphonic/neutts-air.git

# 5. Install the model's dependencies and the package itself
# This runs 'pip install -r requirements.txt' and 'pip install .' from the repo
WORKDIR /neutts-air
RUN pip install --no-cache-dir -r requirements.txt

# 5.1. Copy the /neutts-air/neuttsair folder within the Docker container
RUN cp -r /neutts-air/neuttsair /app

# 6. Delete the cloned repository after installation
# RUN rm -rf /neutts-air

# 7. Set the working directory back to our application folder
WORKDIR /app

# 8. Copy our server's requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 9. Copy the application code into the container
COPY app/main.py .

# 10. Expose the port the app runs on
EXPOSE 8000

# 11. Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]