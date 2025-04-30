"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

interface Story {
  id: string;
  setting: string;
  description: string;
  victim: string;
  suspects: Record<string, string>;
  clues: string[];
  redHerrings: string[];
  culprit: string;
  explanation: string;
}

export default function GamePage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [story, setStory] = useState<Story | null>(null);
  const [currentStage, setCurrentStage] = useState<"start" | "clue_hunt" | "interview" | "guess">("start");
  const [selectedClue, setSelectedClue] = useState<string | null>(null);
  const [selectedSuspect, setSelectedSuspect] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  const generateStory = async () => {
    try {
      const response = await fetch("/api/game/generate", {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message);
      }
      setStory(data);
    } catch (error) {
      setError("Failed to generate story");
    }
  };

  const handleGuess = async (suspect: string) => {
    if (!story) return;

    if (suspect === story.culprit) {
      // Update user progress
      try {
        await fetch("/api/game/progress", {
          method: "POST",
        });
        alert("Congratulations! You solved the case!");
        setStory(null);
        setCurrentStage("start");
      } catch (error) {
        setError("Failed to update progress");
      }
    } else {
      alert("Wrong guess! Try again.");
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">ClueQuest AI</h1>
          <div className="text-gray-400">
            Level: {(session.user as any).progress + 1}
          </div>
        </div>

        {error && (
          <div className="bg-red-500 text-white p-3 rounded mb-4">
            {error}
          </div>
        )}

        {!story ? (
          <div className="text-center">
            <button
              onClick={generateStory}
              className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 transition-colors"
            >
              Start New Case
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-bold mb-4">Case Details</h2>
              <p>{story.description}</p>
              <p className="mt-2">
                <strong>Location:</strong> {story.setting}
              </p>
              <p className="mt-2">
                <strong>Victim:</strong> {story.victim}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-xl font-bold mb-4">Investigation Actions</h3>
                <div className="space-y-4">
                  <button
                    onClick={() => setCurrentStage("clue_hunt")}
                    className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
                  >
                    Look for Clues
                  </button>
                  <button
                    onClick={() => setCurrentStage("interview")}
                    className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
                  >
                    Interview Suspects
                  </button>
                  <button
                    onClick={() => setCurrentStage("guess")}
                    className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition-colors"
                  >
                    Make an Accusation
                  </button>
                </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg">
                {currentStage === "clue_hunt" && (
                  <div>
                    <h3 className="text-xl font-bold mb-4">Found Clues</h3>
                    <div className="space-y-2">
                      {[...story.clues, ...story.redHerrings].map((clue, index) => (
                        <button
                          key={index}
                          onClick={() => setSelectedClue(clue)}
                          className="w-full text-left p-2 hover:bg-gray-700 rounded"
                        >
                          Clue #{index + 1}
                        </button>
                      ))}
                    </div>
                    {selectedClue && (
                      <div className="mt-4 p-4 bg-gray-700 rounded">
                        {selectedClue}
                      </div>
                    )}
                  </div>
                )}

                {currentStage === "interview" && (
                  <div>
                    <h3 className="text-xl font-bold mb-4">Suspects</h3>
                    <div className="space-y-2">
                      {Object.entries(story.suspects).map(([name, info]) => (
                        <button
                          key={name}
                          onClick={() => setSelectedSuspect(name)}
                          className="w-full text-left p-2 hover:bg-gray-700 rounded"
                        >
                          {name}
                        </button>
                      ))}
                    </div>
                    {selectedSuspect && (
                      <div className="mt-4 p-4 bg-gray-700 rounded">
                        {story.suspects[selectedSuspect]}
                      </div>
                    )}
                  </div>
                )}

                {currentStage === "guess" && (
                  <div>
                    <h3 className="text-xl font-bold mb-4">Make Your Accusation</h3>
                    <div className="space-y-2">
                      {Object.keys(story.suspects).map((name) => (
                        <button
                          key={name}
                          onClick={() => handleGuess(name)}
                          className="w-full text-left p-2 hover:bg-gray-700 rounded"
                        >
                          {name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 