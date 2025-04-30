import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { PrismaClient } from "@prisma/client";
import { authOptions } from "../../auth/[...nextauth]/route";

const prisma = new PrismaClient();

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

    // Update user progress
    const updatedUser = await prisma.user.update({
      where: {
        id: user.id,
      },
      data: {
        progress: user.progress + 1,
      },
    });

    return NextResponse.json({
      message: "Progress updated successfully",
      progress: updatedUser.progress,
    });
  } catch (error) {
    console.error("Error updating progress:", error);
    return NextResponse.json(
      { message: "Failed to update progress" },
      { status: 500 }
    );
  }
} 