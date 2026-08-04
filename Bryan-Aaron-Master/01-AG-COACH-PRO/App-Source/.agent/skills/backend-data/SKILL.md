---
name: backend-data
description: Owns Supabase integration, database schema, migrations, authentication, storage, API routes, and Zustand state management. Use when the user asks about database changes, auth issues, adding tables, creating migrations, fixing API routes, managing user data, or state management problems.
---

# Backend & Data Agent

## When to use this skill
- Creating or modifying database tables
- Writing Supabase migrations
- Fixing authentication flows
- Setting up storage buckets
- Building API routes (Expo API routes)
- Modifying Zustand stores
- Adding RLS policies
- Building teacher/admin data queries

## Files Owned
```
lib/supabase.ts
lib/store/auth.ts
lib/store/history.ts
lib/store/quiz.ts
lib/teacher.ts
supabase/migrations/*
app/(auth)/*
app/(admin)/*
app/api/*
types/index.ts
```

## Stack
- **Supabase**: PostgreSQL, Auth (email/password), Storage, Edge Functions
- **Zustand**: Client-side state with AsyncStorage persistence
- **Expo SecureStore**: Sensitive token storage
- **Expo Router API routes**: `app/api/*.ts` for server-side proxying

## Database Schema

### Core Tables (from 001_initial_schema.sql)
```sql
users          (id, email, name, role, school_id, chapter, grade_level)
schools        (id, name, district, region, subscription_tier)
contests       (id, name, category, description, type)
questions      (id, contest_id, question, options, correct_answer, difficulty)
practice_sessions  (id, user_id, contest_id, score, max_score, duration, created_at)
video_submissions  (id, user_id, contest_id, video_url, score, feedback)
user_progress  (id, user_id, contest_id, sessions_completed, best_score, avg_score)
subscriptions  (id, school_id, plan, status, expires_at)
```

### RLS Policy Pattern
```sql
-- Users read/write own data
CREATE POLICY "select_own" ON {table}
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "insert_own" ON {table}
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Teachers read their school's data
CREATE POLICY "teacher_read" ON {table}
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'teacher'
      AND users.school_id = {table}.school_id
    )
  );
```

## Auth Flow
1. **Signup**: email + password → `supabase.auth.signUp()` → create user row → redirect to tabs
2. **Login**: email + password → `supabase.auth.signInWithPassword()` → load session → redirect
3. **Session**: Stored in SecureStore, auto-refreshed by Supabase client
4. **Logout**: `supabase.auth.signOut()` → clear stores → redirect to auth

## State Management (Zustand)

### auth.ts
- `user`: Current user profile
- `session`: Supabase session
- `signIn()`, `signUp()`, `signOut()`
- `initialize()`: Check for existing session on app launch

### history.ts
- `results`: Array of practice results (persisted to AsyncStorage)
- `addResult()`: Add with auto-generated ID and timestamp
- `getResultsByType()`: Filter by contest type
- `clearHistory()`: Reset all results

### quiz.ts
- Active quiz state: questions, current index, answers, timer
- Not persisted (ephemeral per quiz session)

## Migration Template
```sql
-- Migration: {NNN}_{descriptive_name}.sql
-- Purpose: {what this migration does}

-- Tables
CREATE TABLE IF NOT EXISTS {table_name} (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  -- columns here
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_{table}_{column}
  ON {table_name}({column});

-- RLS
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

CREATE POLICY "{table}_select_own" ON {table_name}
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "{table}_insert_own" ON {table_name}
  FOR INSERT WITH CHECK (auth.uid() = user_id);
```

Numbering: `001`, `002`, `003`... sequential. Check existing files first.

## API Route Pattern (Expo Router)
```typescript
// app/api/{name}+api.ts
import { ExpoRequest, ExpoResponse } from 'expo-router/server';

export async function POST(request: ExpoRequest): Promise<ExpoResponse> {
  const body = await request.json();
  // Process with server-side API keys (safe here)
  return ExpoResponse.json({ result: data });
}
```

## Tasks & Priorities
1. **Schema evolution**: Add tables as Contest Builder creates new modules
2. **Offline sync**: Optimistic updates with background sync queue
3. **Teacher dashboard queries**: Analytics, student progress, class management
4. **Storage buckets**: Audio recordings, video submissions
5. **Performance**: Database indexes for common query patterns
6. **Edge Functions**: Server-side logic for sensitive operations

## Rules
1. All schema changes go in migration files (sequential numbering)
2. **Always** use RLS — never bypass security
3. Never store API keys in the database
4. Use parameterized queries — never string concatenation
5. All Zustand stores must have full TypeScript types
6. Foreign keys must reference `auth.users(id)` for user-owned data
7. Always include `created_at` and `updated_at` on new tables
8. Test auth flows on both iOS and Android
9. Include a rollback comment/script with every migration
