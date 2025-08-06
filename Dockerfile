FROM ghcr.io/astral-sh/uv:debian-slim

# Install curl for downloading Tailwind standalone binary
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create a virtual environment and install Python dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -r pyproject.toml

# Copy the rest of the application code
COPY . .

# Download Tailwind CSS standalone binary and build CSS in one step
RUN curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
    && chmod +x tailwindcss-linux-x64 \
    && ./tailwindcss-linux-x64 -i ./snorkelforecast/static/src/input.css -o ./snorkelforecast/static/css/output.css --minify \
    && rm tailwindcss-linux-x64

# Create logs directory for Django logging
RUN mkdir -p logs

# Make startup script executable
RUN chmod +x startup.sh


# Expose port
EXPOSE 8000

# Run startup script
CMD ["./startup.sh"]

