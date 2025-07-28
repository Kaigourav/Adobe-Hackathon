# Step 1: Specify the base image with the correct platform
# Using a slim Python image to keep the size down.
FROM --platform=linux/amd64 python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy your project files into the container
COPY solution.py .

# Step 4: Install dependencies
# PyMuPDF is a powerful and efficient library for PDF manipulation.
# --no-cache-dir helps to keep the image size smaller.
RUN pip install --no-cache-dir PyMuPDF

# Step 5: Create directories for input and output volumes
# These directories will be mounted at runtime.
RUN mkdir -p /app/input /app/output

# Step 6: Define the command to run your solution
# This command is executed when the container starts.
CMD ["python", "solution.py"]