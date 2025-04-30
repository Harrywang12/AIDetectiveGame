# ClueQuest AI

A detective game where players solve AI-generated mysteries.

## Features

- User authentication (login/signup)
- AI-generated mystery stories
- Interactive gameplay with clue hunting and suspect interviews
- Progressive difficulty based on player level
- Modern UI with Tailwind CSS

## Prerequisites

- Node.js 18+ and npm
- Groq API key

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cluequest-ai.git
cd cluequest-ai
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory with the following variables:
```
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000
GROQ_API_KEY=your-groq-api-key-here
```

4. Initialize the database:
```bash
npx prisma generate
npx prisma db push
```

5. Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000.

## Gameplay

1. Create an account or log in
2. Start a new case
3. Investigate the crime scene by:
   - Looking for clues
   - Interviewing suspects
   - Making an accusation
4. Solve the case to progress to the next level

## Technologies Used

- Next.js 14
- TypeScript
- Prisma
- NextAuth.js
- Tailwind CSS
- Groq API

## License

MIT
