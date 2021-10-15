#!/usr/bin/env 

echo "0) SCRIPT $(basename $BASH_SOURCE)"

echo "1) INITIALIZE SERVER VARIABLES"

echo "2) INITIALIZE PROJECT VARIABLES"
BUILD_NUMBER="1.11.3"
BRANCH="$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)"
GIT_HASH="$(git log --pretty=format:'%h' -n 1)"
if [ "${BRANCH}" = "production" ]; then
    ENVIRONMENT="production"
else
    ENVIRONMENT="development"
fi

echo "3) INITIALIZE APPLICATION VARIABLES"
# APPLICATION_HOST="0.0.0.0"
# APPLICATION_PORT="9000"
SERVER="smtp.gmail.com"
PORT="587"
EMAIL_SENDER="yujames33@gmail.com"

SMS_SENDER="+16606282842"

echo "4) EXPORT"
export ENVIRONMENT

# export APPLICATION_HOST
# export APPLICATION_PORT
# export REDIS_HOST
# export REDIS_PORT

export SERVER
export PORT
export EMAIL_SENDER

export SMS_SENDER
