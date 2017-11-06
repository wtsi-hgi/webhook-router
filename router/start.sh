# Run fluent bit
(sleep 45 && /fluent-bit/bin/fluent-bit -c conf/fluent-bit.conf) &

# Run the routing server
node router.js --port 8080 --host 0.0.0.0 --configServer http://configserver:8080