# Run fluent bit
(sleep 45 && /fluent-bit/bin/fluent-bit -c conf/fluent-bit.conf) &

# Run the config server
python -m configserver --client_id=859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.apps.googleusercontent.com \
    --host 0.0.0.0 --port 8080