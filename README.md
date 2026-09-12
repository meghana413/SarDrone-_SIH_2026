# SAR Drone — AI-Based Search and Rescue System

An edge-AI based Search and Rescue (SAR) system designed to assist in detecting victims from aerial imagery, generating optimized routes, and communicating compact rescue information through LoRa.

## 🚁 Project Overview

Search and Rescue operations often involve large areas, difficult terrain, and limited visibility. Manual monitoring of aerial footage can be slow and can increase the workload on rescue teams.

This project develops a software pipeline that processes aerial images/video at the edge, detects potential victims using a custom-trained YOLO11n model, performs image stitching and spatial processing, generates an optimized path using the A\* algorithm, and communicates compact detection information through an ESP32-LoRa communication link.

The system is designed around **edge processing**, reducing the need to continuously transmit large amounts of image or video data.

---

## 🎯 Objectives

- Detect potential victims from aerial imagery using AI.
- Perform detection on edge hardware.
- Process and stitch multiple aerial frames for improved spatial understanding.
- Generate an optimized path using the A\* pathfinding algorithm.
- Communicate compact rescue information using LoRa.
- Provide a software architecture that can be deployed on Raspberry Pi or other edge-computing platforms.
- Build a modular pipeline that can be extended with additional detection classes and navigation capabilities.

---

## 🧠 System Architecture

```text
                 ┌──────────────────┐
                 │      Camera      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Picamera2 /      │
                 │ OpenCV + NumPy   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   YOLO11n        │
                 │ Victim Detection │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Image Stitching  │
                 │ / Spatial        │
                 │ Processing       │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │      A*          │
                 │ Path Planning    │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Compact Detection│
                 │ Data / DCCCC     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │     PySerial     │
                 │ UART             │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │      ESP32       │
                 └────────┬─────────┘
                          │ SPI
                          ▼
                 ┌──────────────────┐
                 │    LoRa SX1276   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Monitoring /     │
                 │ Dashboard        │
                 └──────────────────┘
```
