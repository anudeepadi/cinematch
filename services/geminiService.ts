import { GoogleGenAI, Type } from "@google/genai";
import { TMDB_GENRES } from "../constants";

// Lazy init — avoid crashing at module load when API key is missing
let ai: GoogleGenAI | null = null;
function getAI(): GoogleGenAI | null {
  if (ai) return ai;
  const key = process.env.API_KEY;
  if (!key) return null;
  ai = new GoogleGenAI({ apiKey: key });
  return ai;
}

// Build a genre list string for the prompt
const genreListForPrompt = Object.entries(TMDB_GENRES)
  .map(([id, name]) => `${id}: ${name}`)
  .join('\n');

export interface VibeRecommendation {
  genres: number[];
  keywords: string;
}

// Fallback keyword-to-genre mapping for when Gemini is unavailable
const FALLBACK_VIBES: Record<string, VibeRecommendation> = {
  'action': { genres: [28, 12], keywords: '' },
  'romance': { genres: [10749, 18], keywords: '' },
  'comedy': { genres: [35], keywords: '' },
  'horror': { genres: [27, 53], keywords: '' },
  'sci-fi': { genres: [878], keywords: '' },
  'thriller': { genres: [53, 80], keywords: '' },
  'drama': { genres: [18], keywords: '' },
  'animation': { genres: [16, 10751], keywords: '' },
  'fantasy': { genres: [14, 12], keywords: '' },
  'mystery': { genres: [9648, 53], keywords: '' },
  'war': { genres: [10752, 18], keywords: '' },
  'western': { genres: [37], keywords: '' },
  'documentary': { genres: [99], keywords: '' },
  'musical': { genres: [10402], keywords: '' },
  'sad': { genres: [18, 10749], keywords: '' },
  'happy': { genres: [35, 10751], keywords: '' },
  'scary': { genres: [27, 53], keywords: '' },
  'mind bending': { genres: [878, 9648], keywords: '' },
  'cozy': { genres: [16, 10751, 35], keywords: '' },
  'dark': { genres: [53, 80, 27], keywords: '' },
};

function getFallbackRecommendation(mood: string): VibeRecommendation {
  const lower = mood.toLowerCase();
  for (const [key, value] of Object.entries(FALLBACK_VIBES)) {
    if (lower.includes(key)) return value;
  }
  // Default to popular genres
  return { genres: [28, 18, 53], keywords: '' };
}

export async function getVibeRecommendation(mood: string): Promise<VibeRecommendation> {
  const client = getAI();
  if (!client) {
    console.warn("Gemini API key not configured, using fallback");
    return getFallbackRecommendation(mood);
  }

  try {
    const prompt = `
      The user wants to find movies matching this mood/vibe: "${mood}".

      Here are the available TMDB genre IDs:
      ${genreListForPrompt}

      Based on the mood, return a JSON object with:
      - "genres": an array of 2-4 TMDB genre IDs (numbers) that best match the mood
      - "keywords": a single search keyword that could supplement the genre discovery (or empty string if genres alone are sufficient)

      Be creative in interpreting the mood. For example:
      - "just had a breakup" -> romance + drama genres
      - "can't sleep, need something wild" -> action + thriller genres
      - "rainy day with tea" -> drama + animation genres with "cozy" keyword
    `;

    const response = await client.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            genres: {
              type: Type.ARRAY,
              items: { type: Type.NUMBER },
            },
            keywords: {
              type: Type.STRING,
            },
          },
          required: ["genres", "keywords"],
        },
      },
    });

    const result = JSON.parse(response.text || "{}") as VibeRecommendation;

    // Validate genre IDs exist in our map
    const validGenres = result.genres.filter(id => TMDB_GENRES[id] !== undefined);
    if (validGenres.length === 0) {
      return getFallbackRecommendation(mood);
    }

    return { genres: validGenres, keywords: result.keywords || '' };
  } catch (error) {
    console.error("Gemini vibe recommendation failed, using fallback:", error);
    return getFallbackRecommendation(mood);
  }
}
