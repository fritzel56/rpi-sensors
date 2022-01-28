# Project Overview
This repository holds the code that I'm using read data from sensors for air particulate matter and ambient sound levels to a Raspberry Pi and then stream it to Google Cloud.

## Motivation
My apartment is currently located near a busy intersection. With the arrival of COVID, I started working from home and became much more aware of the volume of traffic going by outside. So I did what any engineer would do: I bought a Raspberry Pi and a couple sensors and started streaming data to the web.

## Architecture Overview
As I've discussed in my other projects, I'm a fan of Google Cloud thanks to their generous free tier. I decided to continue with them, using some old favorites (Functions and BigQuery) plus taking the opportunity to learn some new tools (Pub/Sub, IoT Core, and Data Studio). An overview of the architecture is in the diagram below (note: if you're looking for the icons for the Google Cloud services, you can find them [here](https://cloud.google.com/icons/)).

![RPi Architecture](https://raw.githubusercontent.com/fritzel56/rpi-sensors/readme/images/rpi-architecture.png)
