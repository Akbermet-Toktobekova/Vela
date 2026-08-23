<div align="center">
  <h1>🚀 Vela: Personal Financial Advisor</h1>
  <p><strong>Democratizing access to personalized financial guidance through AI and Multi-Agent Orchestration.</strong></p>
  
  <p>
    <img src="https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge" alt="Status" />
    <img src="https://img.shields.io/badge/Frontend-Expo%20%7C%20React%20Native-blue?style=for-the-badge&logo=react" alt="Expo" />
    <img src="https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/AI-CrewAI-FF5722?style=for-the-badge&logo=robot" alt="CrewAI" />
  </p>
</div>

## 📖 About The Project

Many individuals lack the financial literacy needed to make informed decisions about budgeting, debt, and savings. While free information is abundant, it lacks personalization. Professional advice, on the other hand, is often prohibitively expensive. 

**Vela** is an intelligent, multi-agent financial advisor designed to bridge this gap. It delivers personalized, goal-oriented financial guidance without requiring users to know the "right" questions to ask. By learning from user habits, Vela actively optimizes strategies toward user-defined financial goals.

This project was developed as a BSc Computer Science Thesis, blending **Software Engineering** with deep **Product Management** principles to solve a real-world social challenge: financial inclusion.

## ✨ Key Features

- 💬 **Conversational Interface**: Intuitive chat-based UX for seamless interaction with the AI advisor.
- 🤖 **Multi-Agent Architecture**: Specialized AI agents (Budgeting, Debt Management, Savings) orchestrated by a central coordinator to provide holistic financial strategies.
- 🎯 **Goal-Oriented Optimization**: Proactively works towards user-defined milestones (e.g., paying off a loan, saving for a car).
- 📱 **Daily Micro-Learning**: Delivers bite-sized, highly personalized financial lessons based on the user's current situation.

## 🛠️ Technical Stack

- **Frontend:** Expo (React Native), TypeScript, TailwindCSS (NativeWind)
- **Backend:** Python, FastAPI
- **AI Orchestration:** CrewAI (Multi-Agent System), OpenAI / Anthropic APIs
- **Database:** Firebase Firestore (NoSQL) / MongoDB

## 👩‍💻 Developer & Product Role

This project was built from the ground up by **Akbermet Toktobekova**. 
Operating at the intersection of **Engineering** and **Product Management**, the development process focused heavily on:
- **Product Strategy:** Identifying the core user pain points in financial literacy and designing a solution that is both accessible and highly personalized.
- **System Architecture:** Designing a scalable multi-agent backend capable of handling complex reasoning and routing.
- **UX/UI Implementation:** Ensuring the mobile application feels native, fast, and user-friendly.

## 🚀 Getting Started

### 1. Backend (FastAPI Multi-Agent Server)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
*The FastAPI server will start on `http://127.0.0.1:8000` with interactive Swagger docs at `/docs`.*

### 2. Mobile App (Expo / React Native)
```bash
cd mobile
npm install
npx expo start
```
*Scan the QR code with **Expo Go** (iOS / Android) to launch the app on your physical device!*

---

<div align="center">
  <i>Developed with ❤️ by Akbermet Toktobekova</i>
</div>
