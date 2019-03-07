# Excelsior-Milano-raffle
This script was for the off white presto raffle for Excelsior Milano. As such it is no longer funcitonal. Instead this is meant as a tool to learn how to automate entries in google surveys. This may get your ip banned. You can use proxies by placing them in proxies.txt in the format user:pass@ip:port or just ip:port.
Experiment with the number of threads and number of allowed connections per thread for maximum performace. It can enter thousands of times per minute. 

You can configure some of the settings in config.json:
- use_proxies: set this to true if you want to use proxies placed in proxies.txt file
- catchall: ending email address for a catchall e.g. "easymail.press"
- num_threads: maximum number of threads to run
- max_entries_per_thread: number of entries to run per thread
- max_connections_per_proxy: maximum number of connections that can share a proxy
- exception_timeout: maximum time to wait for each socket
- profiles: list of profiles to enter. see example in config.json
