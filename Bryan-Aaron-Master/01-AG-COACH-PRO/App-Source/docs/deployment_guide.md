# Deployment Guide: AgCoachPro.com

This guide outlines the steps to deploy the **Ag Coach Pro** platform and connect your custom domain for tomorrow's pitch.

## Prerequisites

- **Node.js**: Installed on your machine.
- **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free).
- **Domain Access**: Access to your domain registrar (GoDaddy, Namecheap, etc.) for **AgCoachPro.com**.

---

## Step 1: Export the Web Bundle

Run the following command in your terminal to generate a production-ready web folder:

```bash
npx expo export -p web
```

This will create a `dist` folder in your project root.

---

## Step 2: Deploy to Vercel

I recommend Vercel for its speed and native Expo support.

1. **Install Vercel CLI**:

   ```bash
   npm i -g vercel
   ```

2. **Login & Deploy**:

   ```bash
   vercel login
   vercel
   ```

3. **Deployment Settings**:

   - Link to a new project: **Yes**
   - Project Name: **ag_coach_pro_app**
   - Framework: **Other** or **Create React App**
   - Build Command: `npx expo export -p web` (or `npm run build`)
   - Output Directory: `dist`

---

## Troubleshooting: 404 Errors

If you encounter a 404 error when navigating directly to a page or refreshing your browser, I have added a `vercel.json` file to the root of your project. This file configures Vercel to correctly handle the Single Page Application (SPA) routing used by Expo.

To apply this fix, simply **re-deploy** your project on Vercel after these changes are saved.

---

## Step 3: Connect AgCoachPro.com

1. Go to your project dashboard on Vercel.
2. Navigate to **Settings > Domains**.
3. Add **AgCoachPro.com**.
4. Follow the Vercel instructions to update your DNS records at your registrar:

   - **A Record**: Point `@` to Vercel's IP.
   - **CNAME**: Point `www` to `cname.vercel-dns.com`.

---

## Verification

Once the DNS propagates (usually 15-30 mins), your site will be live!

> [!TIP]
> Use [check-host.net](https://check-host.net) to verify if your DNS changes have propagated globally.
