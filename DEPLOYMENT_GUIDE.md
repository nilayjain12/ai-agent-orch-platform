# 🚀 Full Stack Deployment Guide

To make the AgentOrch platform accessible to others, we will use a "Split Deployment" architecture. This ensures the background AI processes and Telegram bots keep running smoothly.

*   **Database:** Supabase (Free PostgreSQL)
*   **Backend:** Render (Free Web Service)
*   **Frontend:** Vercel (Free Hosting)

Follow these exact steps in order.

---

## Step 1: Set up the Database (Supabase)
We need a cloud database that won't get erased when servers restart.

1. Go to [Supabase](https://supabase.com/) and create a free account.
2. Click **New Project** and select an organization.
3. Give your project a name (e.g., `agentorch-db`) and a strong database password.
4. Select a region close to your users and click **Create new project**.
5. Once provisioned, click the **Settings** gear icon in the left sidebar, then click **Database**.
6. Scroll down to **Connection string** and select the **URI** tab.
7. Copy the connection string. It will look something like this:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxx.supabase.co:5432/postgres`
8. *(Remember to replace `[YOUR-PASSWORD]` with the password you created in step 3).*
9. **Save this URL somewhere safe. This is your `DATABASE_URL`.**

---

## Step 2: Deploy the Backend (Render)
Render will host our Python FastAPI server and run our background Telegram bot 24/7 (or spin it down when inactive on the free tier).

1. Go to [Render](https://render.com/) and sign in with GitHub.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository containing the AgentOrch code.
4. Configure the Web Service:
   *   **Name**: `agentorch-backend`
   *   **Region**: Choose the one closest to your Supabase region.
   *   **Branch**: `main`
   *   **Root Directory**: `backend` (⚠️ *Very Important!*)
   *   **Runtime**: `Python 3`
   *   **Build Command**: `pip install -r requirements.txt`
   *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Scroll down to **Environment Variables** and add the following:
   *   `DATABASE_URL` = *(Paste the Supabase URL from Step 1)*
   *   `GROQ_API_KEY` = *(Your Groq API key)*
   *   `TELEGRAM_BOT_TOKEN` = *(Your Telegram Bot token)*
   *   `CORS_ORIGINS` = `*` *(We will restrict this later once we have the Vercel URL, but `*` is fine for now).*
6. Click **Create Web Service**.
7. Wait a few minutes for it to build and deploy. Once live, copy the public URL provided by Render (e.g., `https://agentorch-backend.onrender.com`).
8. **Save this URL. This is your `BACKEND_URL`.**

---

## Step 3: Deploy the Frontend (Vercel)
Vercel will host our Next.js UI.

1. Go to [Vercel](https://vercel.com/) and sign in with GitHub.
2. Click **Add New Project**.
3. Import your GitHub repository.
4. Configure the Project:
   *   **Project Name**: `agentorch-ui`
   *   **Framework Preset**: `Next.js`
   *   **Root Directory**: Edit this and select `frontend`. (⚠️ *Very Important!*)
5. Open the **Environment Variables** section and add:
   *   **Key**: `NEXT_PUBLIC_API_URL`
   *   **Value**: `[YOUR_BACKEND_URL]/api` *(e.g., `https://agentorch-backend.onrender.com/api`)*
6. Click **Deploy**.
7. Wait 1-2 minutes. Once finished, Vercel will give you a public URL (e.g., `https://agentorch-ui.vercel.app`).

---

## Step 4: Final Polish (Optional but Recommended)
To secure your backend, go back to your **Render** dashboard -> Environment Variables, and update:
*   `CORS_ORIGINS` = `[YOUR_VERCEL_URL]` *(e.g., `https://agentorch-ui.vercel.app`)*

### 🎉 Congratulations!
Your platform is now fully live on the internet! You can share your Vercel URL with anyone, and they can build and execute workflows.
