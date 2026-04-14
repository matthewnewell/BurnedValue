#!/bin/bash
export PATH="/home/matthew/google-cloud-sdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
cd /home/matthew/BurnedValue
gcloud app deploy --project=burned-value-demo --quiet
