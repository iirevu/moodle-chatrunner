
Apparently, cron does not work inside docker containers.
See https://stackoverflow.com/questions/37458287/how-to-run-a-cron-job-inside-a-docker-container

The problem is that cron may die, and will not restart, and this problem has been observed
in practice.
