# Project Overview
This repository holds the code that I'm using read data from sensors to measure air particulate matter levels and ambient sound levels to a Raspberry Pi and then stream it to Google Cloud.

### Table of Contents
**[Motivation](#motivation)**<br>
**[Repo Guide](#repo-guide)**<br>
**[Architecture Overview](#architecture-overview)**<br>
**[Links to Views](#links-to-views)**<br>

## Motivation
My apartment is currently located near a busy intersection. With the arrival of COVID, I started working from home and became much more aware of the volume of traffic going by outside. This in turn caused me to become concerned about the possible environmental impact they might be having on me. So I did what any engineer would do: I bought a Raspberry Pi and a couple sensors and started streaming data to the web.

## Repo Guide
| Folder | Description |
|------|-------------|
| functions | Contains code which is run on a Google Cloud Function to load data from Pub/Sub into BigQuery. |
| gateway | Contains code which is run on Raspberry Pi to pass data to Google Internet of Things (IoT). |
| images | Contains images used in this README. |
| sensors | Contains code run on Raspberry Pi to read data from sensors, write it to a local database, and pass it to the gateway. |

## Architecture Overview
As I've discussed in my other projects, I'm a fan of Google Cloud thanks to their generous free tier. I decided to continue with them, using some old favorites (Functions and BigQuery) plus taking the opportunity to explore some new tools (Pub/Sub, IoT Core, and Data Studio). An overview of the architecture is in the diagram below (note: if you're looking for the icons for the Google Cloud services, you can find them [here](https://cloud.google.com/icons/)).

![RPi Architecture](https://raw.githubusercontent.com/fritzel56/rpi-sensors/readme/images/rpi-architecture.png)

- The sensors connect to the Raspberry Pi via USB. Python is used to collect data from them. See the `sensors` folder for the code used.
- Google Internet of Things (IoT) is build specifically to handle cases like this. There's a good example with code provided [here](https://cloud.google.com/community/tutorials/cloud-iot-gateways-rpi). The Raspberry Pi hosts a MQTT server (see the `gateway` folder) which passes data to IoT's MQTT end point.
- IoT forwards the messages to Pub/Sub (note: using subfolders to direct messages to specific Pub/Sub topics was super helpful). In this case, I route data from all sensors which is to be written to BigQuery to the same topic.
- From here, I considered using Google Dataflow but opted against it as it seemed like overkill (no complicated transformations, aggregations, or filters needed to be applied) and I didn't seem to be able to use it while staying within the free tier. Instead I used Cloud Functions. One specific function is subscribed to the relevant Pub/Sub topic from which it picks up the data, applies a minor transformation, and writes the data to Bigquery (see the `functions` folder).
- Finally I decided to try out Google's visualization tool, data studio, to make vizualizations which could be shared with others.

## Links to Views

If you wish to see the sensor readings, you can find them at the following links:
- Views for the air particulate matter sensor can be found [here](https://datastudio.google.com/reporting/c8f59083-bdd3-4251-b906-5c7bba750328/page/Gi6WC).
- Views for the ambient sound level sensor can be found [here](https://datastudio.google.com/reporting/786a933c-c057-44c3-a1ac-9c4d40a36b8e/page/49pYC)
- Some of my thoughts on the pros and cons of Google Data Studio can be found [here](https://datastudio.google.com/reporting/20df1729-cb84-480b-a0fa-78264c09435b/page/5EBYC/edit)
