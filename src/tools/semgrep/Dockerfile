FROM semgrep/semgrep:latest

# Add custom configuration
COPY rules /rules

# Set working directory
WORKDIR /src

# Default command (can be overridden)
CMD ["--help"] 