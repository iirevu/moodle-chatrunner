# Jobe-in-a-box: a Dockerised Jobe server (see https://github.com/trampgeek/jobe)
# With thanks to David Bowes (d.h.bowes@lancaster.ac.uk) who did all the hard work
# on this originally.

FROM trampgeek/jobeinabox:latest

# Local installations
RUN apt-get update && \
    apt-get install -y python3-requests python3-numpy python3-pandas 
COPY ChatRunner/ /src/
RUN pip install --break-system-packages chatrunner

# Start apache
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
