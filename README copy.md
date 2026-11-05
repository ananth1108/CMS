# MoneyPurse-CMS Content Studio

A local React + FastAPI prototype for managing MoneyPurse-CMS video content from upload through AI-assisted content review and simulated publishing.

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Demonstration workflow

1. Open **Upload Video**.
2. Enter a title and select an MP4, MOV, or WebM file.
3. Open the uploaded item in **AI Content Studio**.
4. Click **Process video**.
5. Review and edit the labelled demo MoneyPurse-CMS transcript and generated content.
6. Save edits, then click **Approve**.
7. Click **Publish** to run the simulated platform publishing result.

The UI marks demo output and demo mode explicitly. It never represents the simulated result as a real social post.

## Environment

Copy `.env.example` to `.env` if provider configuration is needed. The current prototype works without credentials using deterministic demo content.

- `OPENAI_API_KEY`: reserved for a future generation provider.
- `TRANSCRIPTION_PROVIDER`: currently `demo`.

## Current implementation

- FastAPI REST API with SQLite and SQLAlchemy.
- Local video storage under `backend/uploads`.
- File type and 500 MB size validation.
- MoneyPurse-CMS demo transcript and platform-specific Instagram, X, and Telegram content.
- Editable content, approval gate, simulated publish status, and live dashboard KPIs.
- Responsive React/Vite interface with content library and video preview.

Actual FFmpeg transcription, YouTube import, social API publishing, scheduling persistence, authentication, and PostgreSQL/Azure storage are intentionally deferred behind the provider/adaptor boundary for a later release.
