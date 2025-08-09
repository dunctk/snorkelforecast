FROM ghcr.io/astral-sh/uv:debian-slim

# Install curl for downloading Tailwind standalone binary
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the full application code (required since project is installable)
COPY . .

# Install Python dependencies using uv (creates .venv) after code is present
RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"

# Download Tailwind CSS standalone binary and build CSS in one step
RUN curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
    && chmod +x tailwindcss-linux-x64 \
    && rm -f ./snorkelforecast/static/css/output.css \
    && ./tailwindcss-linux-x64 -i ./snorkelforecast/static/src/input.css -o ./snorkelforecast/static/css/output.css --minify \
    && rm tailwindcss-linux-x64

# Fetch and vendor Chart.js locally for self-hosting (place in root static/ so collectstatic picks it up)
RUN mkdir -p ./static/js \
    && curl -fSL https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js -o ./static/js/chart.umd.min.js

# Create logs directory for Django logging
RUN mkdir -p logs

# Make startup script executable
RUN chmod +x startup.sh


# Expose port
EXPOSE 8000

# Run startup script
CMD ["./startup.sh"]
