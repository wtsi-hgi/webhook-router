# Run fluent bit
#(sleep 45 && /fluent-bit/bin/fluent-bit -c conf/fluent-bit.conf) &

# Run the config server
python -m configserver --host 0.0.0.0 --port 8080 --verbose