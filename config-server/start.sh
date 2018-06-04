# Run the config server
python -m configserver --host 0.0.0.0 --port 80 --verbose ${DEBUG_CREDENTIALS:+--debug}