#!/bin/bash
 
NAME="humanitarian-data-service"
FLASKDIR=/home/ec2-user/humanitarian-data-service
#SOCKFILE=/home/ec2-user/humanitarian-data-service/sock
USER=root
#GROUP=wheel
NUM_WORKERS=3
ERROR_LOG=/var/log/gunicorn/error.log
LOG=/var/log/gunicorn/out.log
 
echo "Starting $NAME"
 
# Create the run directory if it doesn't exist
#RUNDIR=$(dirname $SOCKFILE)
#test -d $RUNDIR || mkdir -p $RUNDIR
 
# Start gunicorn
exec gunicorn wsgi:app -b 0.0.0.0:80 \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER \
  --timeout 120 \
  --error-logfile $ERROR_LOG \
  --log-file $LOG
  
# --user=$USER --group=$GROUP \
# --bind=unix:$SOCKFILE -m 007
