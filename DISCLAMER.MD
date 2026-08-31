# DISCLAIMER AND LEGAL NOTICE

This document outlines the limitations, responsibilities, and terms of use regarding the detection and redaction of Personally Identifiable Information (PII) using the WaveRedact software.

## ⚠️ No Guarantee of Accuracy (AS IS)
WaveRedact utilizes Artificial Intelligence, Natural Language Processing, and Automatic Speech Recognition models. Due to the probabilistic nature of these technologies, the detection is not infallible.
* **Margin of Error:** The models may generate *false negatives* (failing to detect sensitive PII) or *false positives* (redacting harmless data).
* **"AS IS" Provision:** The software is provided "as is", without any express or implied warranty of absolute accuracy, merchantability, or fitness for the purpose of guaranteed data protection.

## 🛡️ User Responsibility (Compliance)
The developer and maintainers of WaveRedact assume no liability for any data leaks, privacy breaches, or regulatory violations resulting from the use of this tool.
* **Human-in-the-Loop Required:** WaveRedact is designed solely to *assist* and accelerate anonymization workflows. The output must always be validated by a human operator before any data is shared or published.
* **Regulatory Compliance:** The end-user remains strictly and solely responsible for compliance with all applicable data protection and privacy laws (e.g., GDPR, HIPAA, CCPA) regarding the processed files.

## 🔒 Local Processing (Privacy by Design)
WaveRedact was architected to maximize security by operating as a fully isolated, air-gapped compatible system.
* **Offline Execution:** The entire audio and AI processing pipeline (ASR and LLM inference) runs strictly locally on the user's hardware.
* **No Data Transfer:** No audio data, transcripts, or extracted PII are ever transmitted to external servers, cloud APIs, or the developer. The user retains absolute control as the sole Data Controller.

## ⚖️ Limitation of Liability
In no event shall the author or copyright holders be held liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, legal penalties, loss of data, or business interruption) arising in any way out of the use of, or inability to use, this software.