import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { PrismaClient } from "@prisma/client";
import { Groq } from "groq";
import { authOptions } from "../../auth/[...nextauth]/route";

const prisma = new PrismaClient();
const client = new Groq({ apiKey: process.env.GROQ_API_KEY! });

export async function POST(request: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json(
        { message: "Unauthorized" },
        { status: 401 }
      );
    }

    const user = await prisma.user.findUnique({
      where: {
        id: (session.user as any).id,
      },
    });

    if (!user) {
      return NextResponse.json(
        { message: "User not found" },
        { status: 404 }
      );
    }

    const level = user.progress + 1;
    const difficulty = "Medium"; // You can adjust this based on level

    const prompt = `You are a mystery story generator. Create a random detective story for level ${level} with:
- A setting (e.g., mansion, park, office).
- A description of what crime happened.
- A victim and their backstory.
- 4 suspects, each with motives and alibis.
- ${Math.max(3 - Math.floor(level / 5), 1)} key clues.
- ${2 + Math.floor(level / 5)} red herrings.
- One culprit.
- An explanation of why the culprit committed the crime.
- Make it a ${difficulty}.

Provide the output in JSON format:
{
    "setting": "",
    "description": "",
    "victim": "",
    "suspects": {
        "<Suspect 1 Full Name>": "",
        "<Suspect 2 Full Name>": "",
        "<Suspect 3 Full Name>": "",
        "<Suspect 4 Full Name>": ""
    },
    "clues": [],
    "red_herrings": [],
    "culprit": "",
    "explanation": ""
}

Only output the JSON part.
Only output the first and last name for the culprit, no prefixes such as Dr or Mr or Mrs or Ms.
Don't explain why they are red herrings.`;

    const completion = await client.chat.completions.create({
      model: "llama3-70b-8192",
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
      temperature: 1,
      max_tokens: 1024,
      top_p: 1,
      stream: false,
    });

    const story = JSON.parse(completion.choices[0].message.content);

    // Save the story to the database
    const savedStory = await prisma.story.create({
      data: {
        setting: story.setting,
        description: story.description,
        victim: story.victim,
        suspects: story.suspects,
        clues: story.clues,
        redHerrings: story.red_herrings,
        culprit: story.culprit,
        explanation: story.explanation,
      },
    });

    return NextResponse.json(savedStory);
  } catch (error) {
    console.error("Error generating story:", error);
    return NextResponse.json(
      { message: "Failed to generate story" },
      { status: 500 }
    );
  }
} 