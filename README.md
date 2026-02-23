
# 🎓 AI-Powered Learning Management System (LMS)

> A modern, hybrid-cloud educational platform that uses AI to automatically transcribe and summarize lecture videos.

![Project Status](https://img.shields.io/badge/Status-Active_Development-green)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI_React_Firebase_Azure-blue)

## 📖 Overview

This LMS is designed to bridge the gap between video hosting and active learning. When an instructor uploads a lecture, the system automatically:
1.  **Secures** the video in Azure Blob Storage.
2.  **Transcribes** the audio using Azure Speech Services.
3.  **Summarizes** the content into study notes using Azure OpenAI (GPT).
4.  **Updates** the student dashboard in real-time via Firebase Firestore.

## 🚀 Key Features

*   **🤖 Automated AI Pipeline:** Background tasks handle heavy video processing (Speech-to-Text & LLM Summarization) without blocking the UI.
*   **☁️ Secure Video Streaming:** Uses Time-Limited SAS (Shared Access Signature) tokens so videos cannot be downloaded or shared publicly.
*   **⚡ Real-Time Updates:** Students see status changes (Processing → Completed) instantly via Firestore listeners.
*   **🔐 Role-Based Access:** Distinct portals for **Instructors** (Upload & Manage) and **Students** (Watch & Learn).
*   **🔑 Modern Auth:** Google Sign-In managed by Firebase Authentication.

---

## 🛠️ Tech Stack

### Backend
*   **Framework:** FastAPI (Python)
*   **Database:** Cloud Firestore (NoSQL)
*   **AI Services:** Azure Cognitive Services (Speech), Azure OpenAI
*   **Storage:** Azure Blob Storage
*   **Task Management:** FastAPI BackgroundTasks

### Frontend
*   **Framework:** React (Vite)
*   **Styling:** CSS3 (Custom Dashboard Layout)
*   **State/Data:** Firebase SDK (Auth, Firestore)
*   **HTTP Client:** Axios (with Interceptors for Security)

---

## 📂 Project Structure

```text
📦Learning_Management_System
 ┣ 📂backend
 ┃ ┣ 📂ai_features
 ┃ ┃ ┣ 📜router.py
 ┃ ┃ ┣ 📜schemas.py
 ┃ ┃ ┣ 📜services.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂core
 ┃ ┃ ┣ 📜config.py
 ┃ ┃ ┣ 📜database.py
 ┃ ┃ ┣ 📜firebase_config.json
 ┃ ┃ ┣ 📜security.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂courses
 ┃ ┃ ┣ 📜router.py
 ┃ ┃ ┣ 📜schemas.py
 ┃ ┃ ┣ 📜services.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📜.env
 ┃ ┣ 📜.gitignore
 ┃ ┣ 📜main.py
 ┃ ┗ 📜requirements.txt
 ┣ 📂frontend
 ┃ ┣ 📂node_modules
 ┃ ┣ 📂src
 ┃ ┃ ┣ 📂components
 ┃ ┃ ┃ ┣ 📜InstructorDashboard.jsx
 ┃ ┃ ┃ ┣ 📜Login.jsx
 ┃ ┃ ┃ ┗ 📜StudentDashboard.jsx
 ┃ ┃ ┣ 📜api.js
 ┃ ┃ ┣ 📜App.css
 ┃ ┃ ┣ 📜App.jsx
 ┃ ┃ ┣ 📜firebase.js
 ┃ ┃ ┗ 📜main.jsx
 ┃ ┣ 📜.gitignore
 ┃ ┣ 📜current-flow.png
 ┃ ┣ 📜eslint.config.js
 ┃ ┣ 📜index.html
 ┃ ┣ 📜package-lock.json
 ┃ ┣ 📜package.json
 ┃ ┗ 📜vite.config.js
 ┣ 📂venv
 ┣ 📜.gitignore
 ┗ 📜README.md
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Node.js (v16+)
*   Python (v3.9+)
*   Azure Cloud Account (Speech, OpenAI, Storage resources enabled)
*   Firebase Project (Auth & Firestore enabled)

### 2. Backend Setup

Navigate to the backend folder:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

**Configuration:**
1.  Create a `.env` file in `backend/` and add your Azure keys:
    ```env
    AZURE_SPEECH_KEY=your_speech_key
    AZURE_SPEECH_ENDPOINT=your_speech_endpoint
    AZURE_OPENAI_ENDPOINT=your_openai_endpoint
    AZURE_OPENAI_API_KEY=your_openai_key
    AZURE_OPENAI_DEPLOYMENT=gpt-4o
    AZURE_OPENAI_API_VERSION=2023-05-15
    AZURE_STORAGE_ACCOUNT_URL=https://youraccount.blob.core.windows.net
    BLOB_CONTAINER_NAME=videos    ```
2.  Place your Firebase Admin SDK JSON file in `backend/core/` and rename it to `firebase_config.json`.

**Run the Server:**
```bash
uvicorn main:app --reload
```
*Server will start at `http://localhost:8000`*

### 3. Frontend Setup

Open a new terminal and navigate to the frontend folder:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

**Configuration:**
Ensure `src/firebase.js` is updated with your specific Firebase Client Config (API Key, Auth Domain, Project ID).

**Run the Client:**
```bash
npm run dev
```
*Client will start at `http://localhost:5173` (usually)*

---

## 🎮 Usage Guide

1.  **Login:** Open the frontend. Sign in using **Google**.
    *   *Note: First-time users are defaulted to the 'Student' role.*
2.  **Instructor Role (Setup):** Manually change your role to `instructor` in the Firestore `users` collection to access the upload dashboard.
3.  **Upload:** Go to the Instructor Dashboard, select an `.mp4` file, and click **Upload**.
4.  **Processing:**
    *   The file uploads to Azure.
    *   FastAPI triggers the AI pipeline.
    *   Status updates from `processing` → `transcribing` → `summarizing`.
5.  **Learning:**
    *   Switch to the Student Dashboard.
    *   Click the video title.
    *   Watch the video and read the generated AI summary.

---

## 🛡️ Security Note

*   **Backend:** Validates Firebase ID Tokens via the `Authorization: Bearer` header before processing requests.
*   **Video Access:** Videos are private. The backend generates a temporary SAS URL (valid for 24h) only for authenticated users.

---

## 📝 License

This project is open-source and available under the MIT License.