# FFA Training App - Complete Starter Code

## 🎯 Project Overview

A comprehensive mobile training application for Texas FFA students to practice all 29 Career Development Events (CDEs) and 11 Leadership Development Events (LDEs).

**Target:** 20,000 students across 400 Texas FFA chapters
**Pricing:** $450/school/year subscription
**Tech Stack:** React Native (Expo) + Supabase + AI Services

---

## 📋 Prerequisites

Before starting, make sure you have:

- **Node.js** (v18 or higher): https://nodejs.org/
- **Git**: https://git-scm.com/
- **Expo CLI**: We'll install this together
- **Code Editor**: VS Code recommended
- **Supabase Account**: https://supabase.com (free tier)

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies

```bash
# Install Expo CLI globally
npm install -g expo-cli

# Navigate to project directory
cd ffa-training-app

# Install all dependencies
npm install
```

### Step 2: Setup Supabase

1. Go to https://supabase.com and create a free account
2. Create a new project (name it "ffa-training-app")
3. Wait for database to provision (~2 minutes)
4. Go to Project Settings → API
5. Copy your `Project URL` and `anon public` key

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Supabase credentials:
# EXPO_PUBLIC_SUPABASE_URL=your-project-url
# EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Step 4: Setup Database Schema

```bash
# This will create all necessary tables
npm run db:setup
```

### Step 5: Start Development

```bash
# Start the Expo development server
npm start

# Then:
# - Press 'i' for iOS simulator (Mac only)
# - Press 'a' for Android emulator
# - Scan QR code with Expo Go app on your phone
```

---

## 📁 Project Structure

```
ffa-training-app/
├── app/                          # Main application code (Expo Router)
│   ├── (auth)/                  # Authentication screens
│   │   ├── login.tsx
│   │   └── signup.tsx
│   ├── (tabs)/                  # Main app tabs
│   │   ├── _layout.tsx
│   │   ├── index.tsx           # Home/Dashboard
│   │   ├── cde.tsx             # CDE Practice
│   │   ├── lde.tsx             # LDE Practice
│   │   └── profile.tsx         # User Profile
│   ├── contest/                 # Individual contest screens
│   │   ├── [id].tsx            # Dynamic contest screen
│   │   └── _layout.tsx
│   └── _layout.tsx             # Root layout
│
├── components/                  # Reusable UI components
│   ├── ui/                     # Basic UI elements
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Loading.tsx
│   ├── contest/                # Contest-specific components
│   │   ├── QuizQuestion.tsx
│   │   ├── VideoRecorder.tsx
│   │   └── ScoreCard.tsx
│   └── dashboard/              # Dashboard components
│       ├── ProgressChart.tsx
│       └── RecentActivity.tsx
│
├── lib/                        # Core functionality
│   ├── supabase.ts            # Supabase client setup
│   ├── auth.ts                # Authentication helpers
│   ├── database.ts            # Database queries
│   ├── ai/                    # AI integrations
│   │   ├── whisper.ts         # Speech-to-text
│   │   ├── claude.ts          # Text analysis
│   │   └── mediapipe.ts       # Video analysis
│   └── scoring/               # Scoring algorithms
│       ├── creed.ts
│       ├── quiz.ts
│       └── interview.ts
│
├── supabase/                   # Supabase configuration
│   ├── migrations/            # Database migrations
│   │   └── 001_initial_schema.sql
│   ├── functions/             # Edge functions
│   │   └── analyze-video/
│   └── config.toml
│
├── types/                      # TypeScript type definitions
│   ├── database.ts
│   ├── contest.ts
│   └── user.ts
│
├── constants/                  # App constants
│   ├── Contests.ts            # Contest metadata
│   ├── Colors.ts
│   └── Rules.ts               # Official FFA rules
│
├── assets/                     # Static assets
│   ├── images/
│   ├── fonts/
│   └── rules/                 # Contest rule PDFs
│
├── .env.example               # Environment template
├── .env                       # Your local config (gitignored)
├── package.json
├── tsconfig.json
├── app.json                   # Expo config
└── README.md
```

---

## 🗄️ Database Schema Overview

### Core Tables

1. **users** - User accounts and profiles
2. **schools** - FFA chapter information
3. **contests** - CDE/LDE contest definitions
4. **questions** - CDE practice questions
5. **practice_sessions** - User practice history
6. **video_submissions** - LDE video recordings
7. **scores** - Performance tracking
8. **subscriptions** - School subscriptions

---

## 🎨 Features Included in Starter

### ✅ Authentication System
- Email/password signup and login
- Protected routes
- Session management
- Profile management

### ✅ Contest Management
- All 29 CDEs defined
- All 11 LDEs defined
- Contest rules and metadata
- Question bank structure

### ✅ Basic UI Components
- Custom button, input, card components
- Loading states
- Error handling
- Responsive layouts

### ✅ Database Integration
- Supabase client configured
- Type-safe queries
- Real-time subscriptions ready
- File storage setup

### ✅ Navigation
- Tab-based navigation
- Stack navigation for contests
- Deep linking ready
- Back navigation

---

## 📱 Development Workflow

### Running the App

```bash
# Start development server
npm start

# Run on iOS (Mac only)
npm run ios

# Run on Android
npm run android

# Run on web
npm run web
```

### Database Management

```bash
# Apply new migrations
npm run db:migrate

# Reset database (careful!)
npm run db:reset

# View database in browser
npm run db:studio
```

### Type Generation

```bash
# Generate TypeScript types from Supabase
npm run types:generate
```

---

## 🔐 Environment Variables

Create a `.env` file with these variables:

```env
# Supabase
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# OpenAI (for speech-to-text)
OPENAI_API_KEY=your-openai-key

# Anthropic (for AI feedback)
ANTHROPIC_API_KEY=your-anthropic-key

# App Config
EXPO_PUBLIC_APP_ENV=development
```

---

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- VideoRecorder.test.tsx
```

---

## 📦 Building for Production

### iOS

```bash
# Build for iOS
eas build --platform ios

# Submit to App Store
eas submit --platform ios
```

### Android

```bash
# Build for Android
eas build --platform android

# Submit to Play Store
eas submit --platform android
```

---

## 🎯 Next Steps

After setup, you can:

1. **Build First Feature**: Start with Creed Speaking (in `/app/contest/creed-speaking.tsx`)
2. **Add Questions**: Populate CDE question banks
3. **Implement Scoring**: Add AI-powered scoring algorithms
4. **Create Dashboard**: Build teacher analytics
5. **Test with Users**: Get feedback from pilot schools

---

## 📚 Documentation Links

- **Expo Docs**: https://docs.expo.dev/
- **Supabase Docs**: https://supabase.com/docs
- **React Native**: https://reactnative.dev/docs/getting-started
- **TypeScript**: https://www.typescriptlang.org/docs/

---

## 🆘 Getting Help

If you run into issues:

1. Check the error message carefully
2. Search the issue in our docs
3. Ask Claude for debugging help
4. Check Expo/Supabase forums

---

## 📝 License

Proprietary - All rights reserved

---

## 👥 Team

Built with AI assistance for Texas FFA students.

**Ready to change how students practice for FFA contests!** 🚀
