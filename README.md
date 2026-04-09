# ☁️ Mini Secure Cloud Storage System

https://cloud-project1-8619.onrender.com

## 📌 Project Overview

A secure cloud-based file storage system that enables users to upload, store, and retrieve files using encryption and file splitting techniques to ensure data security and integrity.

## 🎯 Objectives

* To implement a mini cloud storage system
* To ensure secure file handling using encryption
* To maintain data integrity during upload/download
* To simulate real-world cloud storage concepts

## 🚀 Key Features

* File upload and download system
* Encryption of files before storage
* Splitting files into multiple parts
* Decryption and merging during download
* User authentication system
* Database integration for metadata

## ⚙️ Working Principle

1. User uploads a file
2. File is divided into multiple chunks
3. Each chunk is encrypted
4. Encrypted chunks are stored securely
5. On download:

   * Chunks are retrieved
   * Decrypted
   * Merged back into original file

## 🧩 Tech Stack

### 🔹 Backend

* Python
* Flask (Web Framework)

### 🔹 Frontend

* HTML
* CSS

### 🔹 Database

* SQLite

### 🔹 Security

* Encryption (AES-based logic)
* File chunking and merging

### 🔹 Tools and Platforms

* Git and GitHub (Version Control)
* Render (Backend Deployment)
* Vercel (Frontend or Demo Deployment)

## 🏗️ System Architecture

* Client (Browser UI)
* Flask Server (Application Logic)
* File Processing Module (Encryption, Splitting, Merging)
* Database (Metadata Storage)
* Local or Server Storage

## 🔄 Data Flow

Upload Flow:

1. User uploads file via UI
2. Backend processes file
3. File is split into chunks
4. Each chunk is encrypted
5. Stored in server storage
6. Metadata saved in database

Download Flow:

1. Fetch encrypted chunks
2. Decrypt each chunk
3. Merge chunks
4. Return original file to user

## 🛠️ Development Tools

* VS Code (Code Editor)
* Python Virtual Environment (venv)
* Postman (optional for API testing)

## 📦 Modules Used

* Flask (routing and server handling)
* OS (file handling)
* SQLite3 (database operations)
* Custom modules: encryption_utils.py, file_manager.py, database.py

## 📊 Project Type

* Cloud Computing Mini Project
* Web-based Application
* Security-focused File Storage System

## 🔐 Security Mechanism

* Encryption ensures data confidentiality
* File splitting prevents direct reconstruction
* Integrity checks ensure no data loss
* Secure storage of metadata

## ☁️ Deployment Platforms

* Render for backend deployment
* Vercel for demonstration or frontend hosting

## 📊 Advantages

* Secure data storage
* Efficient file management
* Prevents unauthorized access
* Lightweight and easy to deploy

## ⚠️ Limitations

* Not fully distributed (single-node system)
* Limited scalability
* Basic user interface
* Suitable for academic or demo purposes

## 💡 Future Scope

* Multi-node distributed storage system
* Advanced user roles and permissions
* File sharing functionality
* Improved UI and UX
* Integration with cloud providers

## 👨‍💻 Author

Swaraj Gondchawar

## 📄 Conclusion

This project demonstrates how cloud storage systems work by combining encryption, file splitting, and secure retrieval, providing a strong foundation for building advanced distributed cloud applications.
