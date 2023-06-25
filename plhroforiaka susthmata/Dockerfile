# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Flask app to the working directory
COPY . .

# Expose the port that the Flask app will run on
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
