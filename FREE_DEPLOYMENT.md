# Free Deployment Guide

This guide is for a zero-budget deployment. It uses only free tiers or self-hosted services.

## Important Reality Check

- A truly free public deployment is possible only with tradeoffs.
- Cloud AI providers are usually not fully free forever.
- The most reliable zero-cost path is to use free hosting for the frontend and tunnel a backend you run yourself, or use a free-tier backend host with sleep limits.

## Recommended Free Architecture

### Option A: Most Reliable Free Path

- Frontend: Vercel free tier.
- Backend: your own PC or an always-on free local machine.
- Public access: Cloudflare Tunnel free tier.
- Model: local llama.cpp on your machine, or a free-tier cloud model API if available.

### Option B: All-Cloud Free-Tier Path

- Frontend: Vercel free tier.
- Backend: a free-tier host such as Render, Railway, or Fly.io if the account offers a free plan.
- Model: a provider with free quota or trial credits only.

## Before Deployment Checklist

1. Remove placeholder secrets from [.env.example](.env.example).
2. Choose your free hosting path: Option A or Option B.
3. Decide whether the model will run locally or through a free-tier cloud API.
4. Generate a strong `JWT_SECRET_KEY`.
5. Set `FRONTEND_URL` and `ALLOWED_ORIGINS` to the public URL you will actually use.
6. Confirm the app starts locally with `python enhanced_api.py` and `npm run build` in `frontend`.
7. Make sure all uploads and health checks work locally.

## Step-by-Step: Option A, Most Reliable Free Path

### Step 1: Prepare the backend machine

- Use your PC or any machine that can stay online.
- Install Python 3.10+ and Node.js 18+.
- Clone the repository.
- Create a `.env` file from [.env.example](.env.example).

### Step 2: Configure environment variables

- Set `ENVIRONMENT=production`.
- Set `JWT_SECRET_KEY` to a long random value.
- Set `DEFAULT_MODEL_PROVIDER=core` if you want local model inference.
- If you want free-tier cloud inference, set the provider key and API key only if you have one.
- Set `FRONTEND_URL` to the public site URL you plan to use.
- Set `ALLOWED_ORIGINS` to the same public URL.

### Step 3: Install backend dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements_enterprise.txt
```

### Step 4: Run the backend locally

```bash
python enhanced_api.py
```

### Step 5: Deploy the frontend for free

- Create a free Vercel account.
- Import the `frontend/` folder as the app.
- Set `NEXT_PUBLIC_API_URL` to the public backend URL if the backend is remote.
- If frontend and backend share one public origin behind a tunnel or proxy, leave `NEXT_PUBLIC_API_URL` blank.

### Step 6: Expose the backend publicly for free

- Install Cloudflare Tunnel on the backend machine.
- Create a tunnel that points to the local backend port.
- Map the tunnel hostname to the backend service.
- Set `FRONTEND_URL` and `ALLOWED_ORIGINS` to the tunnel or frontend domain.

### Step 7: Start the app

- Start the backend.
- Start the frontend deployment.
- Verify `/api/health` and the main chat page open successfully.

## Step-by-Step: Option B, All-Cloud Free-Tier Path

### Step 1: Create the frontend deployment

- Deploy `frontend/` to Vercel free tier.
- Set the frontend environment variable if the backend is on a different domain.

### Step 2: Create the backend deployment

- Deploy the FastAPI backend to a free-tier host if your account has one.
- Use `Dockerfile.backend` or the native Python start command depending on host support.
- Mount persistent storage if the host allows it.

### Step 3: Configure cloud model access

- Choose one provider only.
- Add its API key to the host environment.
- Set `DEFAULT_MODEL_PROVIDER` to that provider.

### Step 4: Connect the services

- Set `FRONTEND_URL` to the frontend domain.
- Set `ALLOWED_ORIGINS` to the frontend domain.
- Set `NEXT_PUBLIC_API_URL` to the backend domain if the frontend is separate.

## Free Deployment Checklist After Launch

1. Test login and session creation.
2. Test `/api/health`.
3. Test one chat message.
4. Test one voice upload.
5. Test one image upload.
6. Test a page refresh and confirm data persistence.
7. Confirm CORS and cookies work from the public domain.
8. Confirm the app does not point to localhost anywhere.

## Free Limitations

- Free hosts can sleep or throttle requests.
- Free cloud inference may run out of quota.
- Free plans are fine for demo, MVP, or small personal use.
- For serious patient traffic, paid hosting is the real production option.
