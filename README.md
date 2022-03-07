# SingStruments
A an AI-Driven Website that estimates your notes as you sing, and converts them into other instruments

## SPICE
Uses TFHub Version of SPICE: Self-Supervised Pitch Estimation. This takes the user recording and uses it to estimate the pitch of the notes sung. It then uses this to convert the notes into other instruments.

## Running
May be run by pulling the docker image from the dockerhub:
```
docker run -d -p 8000:8000 ijtan/interfaces_assignment
```

Then go to http://localhost:8000/