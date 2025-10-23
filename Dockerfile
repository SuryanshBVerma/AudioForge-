# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory for the application
WORKDIR /app

# 3. Install espeak and git, which are required
RUN apt-get update && apt-get install -y espeak git build-essential cmake && rm -rf /var/lib/apt/lists/*


# 7. Set the working directory back to our application folder
WORKDIR /app

# Copy the entire application folder into the container
COPY app/ /app/
RUN pip install --no-cache-dir -r requirements.txt


# 10. Expose the port the app runs on
EXPOSE 8000

# 11. Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]