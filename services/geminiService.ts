import { GoogleGenAI, Type } from "@google/genai";
import { MOVIE_DB } from "../constants";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const getMovieRecommendations = async (mood: string): Promise<string[]> => {
  try {
    const movieTitles = MOVIE_DB.map(m => m.title);
    
    const prompt = `
      The user is looking for movies that fit this specific mood or vibe: "${mood}".
      
      Here is the list of available movies:
      ${JSON.stringify(movieTitles)}

      Select exactly 10 movies from the list that best match the described mood.
      Return ONLY the exact titles of the movies in a JSON array.
    `;

    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: { type: Type.STRING },
        },
      },
    });

    const recommendedTitles = JSON.parse(response.text || "[]") as string[];
    
    // Map titles back to IDs
    const recommendedIds = recommendedTitles
      .map(title => MOVIE_DB.find(m => m.title === title)?.id)
      .filter((id): id is string => !!id);

    return recommendedIds;
  } catch (error) {
    console.error("Error fetching recommendations:", error);
    return [];
  }
};
