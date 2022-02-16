# Project Overview
This repository holds the code that I'm using read data from sensors for air particulate matter and ambient sound levels to a Raspberry Pi and then stream it to Google Cloud.

### Table of Contents
**[Motivation](#motivation)**<br>
**[Repo Guide](#repo-guide)**<br>
**[Architecture Overview](#architecture-overview)**<br>

## Motivation
My apartment is currently located near a busy intersection. With the arrival of COVID, I started working from home and became much more aware of the volume of traffic going by outside. So I did what any engineer would do: I bought a Raspberry Pi and a couple sensors and started streaming data to the web.

## Repo Guide
| Folder | Description |
|------|-------------|
| functions | Contains code which is run on a Google Cloud Function to load data from Pub/Sub into BigQuery. |
| gateway | Contains code which is run on Raspberry Pi to pass data to Google Internet of Things (IoT). |
| images | Contains images used in this README. |
| sensors | Contains code run on Raspberry Pi to read data from sensors, write it to a local database, and pass it to the gateway. |

## Architecture Overview
As I've discussed in my other projects, I'm a fan of Google Cloud thanks to their generous free tier. I decided to continue with them, using some old favorites (Functions and BigQuery) plus taking the opportunity to learn some new tools (Pub/Sub, IoT Core, and Data Studio). An overview of the architecture is in the diagram below (note: if you're looking for the icons for the Google Cloud services, you can find them [here](https://cloud.google.com/icons/)).

![RPi Architecture](https://raw.githubusercontent.com/fritzel56/rpi-sensors/readme/images/rpi-architecture.png)
