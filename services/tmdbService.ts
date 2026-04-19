import { Movie, Genre, TMDBMovieRaw, TMDBMovieDetail, TMDBCredits, TMDBMovieListResponse } from '../types';
import { TMDB_GENRES } from '../constants';

const BASE_URL = 'https://api.themoviedb.org/3';
const IMAGE_BASE = 'https://image.tmdb.org/t/p';
const API_KEY = process.env.TMDB_API_KEY;

function apiUrl(path: string, params: Record<string, string> = {}): string {
  const url = new URL(`${BASE_URL}${path}`);
  url.searchParams.set('api_key', API_KEY!);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }
  return url.toString();
}

// --- Image URLs ---

export function getPosterUrl(posterPath: string, size: string = 'w342'): string {
  return `${IMAGE_BASE}/${size}${posterPath}`;
}

export function getBackdropUrl(backdropPath: string, size: string = 'w780'): string {
  return `${IMAGE_BASE}/${size}${backdropPath}`;
}

// --- Genre Map ---

let genreMapCache: Record<number, string> | null = null;

async function fetchGenreMap(): Promise<Record<number, string>> {
  if (genreMapCache) return genreMapCache;

  try {
    const res = await fetch(apiUrl('/genre/movie/list', { language: 'en' }));
    const data = await res.json();
    const map: Record<number, string> = {};
    for (const g of data.genres) {
      map[g.id] = g.name;
    }
    genreMapCache = map;
    return map;
  } catch {
    // Fallback to hardcoded genres
    return TMDB_GENRES;
  }
}

// --- Mapping ---

function mapTMDBToMovie(raw: TMDBMovieRaw, genreMap: Record<number, string>): Movie {
  const genres: Genre[] = raw.genre_ids
    .map(id => ({ id, name: genreMap[id] || 'Unknown' }))
    .filter(g => g.name !== 'Unknown');

  const year = raw.release_date ? parseInt(raw.release_date.substring(0, 4), 10) : 0;

  return {
    id: String(raw.id),
    title: raw.title,
    year,
    genre: genres.map(g => g.name).join(', ') || 'Unknown',
    genres,
    description: raw.overview || 'No description available.',
    rating: Math.round(raw.vote_average * 10) / 10,
    language: raw.original_language.toUpperCase(),
    poster_path: raw.poster_path!,
    backdrop_path: raw.backdrop_path || undefined,
    release_date: raw.release_date,
  };
}

// --- List Endpoints ---

export async function fetchPopularMovies(page: number = 1): Promise<Movie[]> {
  const genreMap = await fetchGenreMap();
  const res = await fetch(apiUrl('/movie/popular', { language: 'en-US', page: String(page) }));
  const data: TMDBMovieListResponse = await res.json();

  return data.results
    .filter(m => m.poster_path !== null)
    .map(m => mapTMDBToMovie(m, genreMap));
}

export async function searchMovies(query: string): Promise<Movie[]> {
  const genreMap = await fetchGenreMap();
  const res = await fetch(apiUrl('/search/movie', { query, language: 'en-US', page: '1' }));
  const data: TMDBMovieListResponse = await res.json();

  return data.results
    .filter(m => m.poster_path !== null)
    .map(m => mapTMDBToMovie(m, genreMap));
}

export async function discoverByGenres(genreIds: number[], keywords?: string): Promise<Movie[]> {
  const genreMap = await fetchGenreMap();
  const params: Record<string, string> = {
    language: 'en-US',
    sort_by: 'popularity.desc',
    with_genres: genreIds.join(','),
  };
  if (keywords) {
    params.with_keywords = keywords;
  }

  const res = await fetch(apiUrl('/discover/movie', params));
  const data: TMDBMovieListResponse = await res.json();

  return data.results
    .filter(m => m.poster_path !== null)
    .map(m => mapTMDBToMovie(m, genreMap));
}

// --- Detail Endpoints ---

const detailCache = new Map<number, { tagline: string; runtime: number; genres: Genre[] }>();
const creditsCache = new Map<number, { director: string; cast: string[] }>();

export async function fetchMovieDetails(id: number): Promise<{ tagline: string; runtime: number; genres: Genre[] }> {
  if (detailCache.has(id)) return detailCache.get(id)!;

  const res = await fetch(apiUrl(`/movie/${id}`, { language: 'en-US' }));
  const data: TMDBMovieDetail = await res.json();

  const result = {
    tagline: data.tagline || '',
    runtime: data.runtime || 0,
    genres: data.genres || [],
  };
  detailCache.set(id, result);
  return result;
}

export async function fetchMovieCredits(id: number): Promise<{ director: string; cast: string[] }> {
  if (creditsCache.has(id)) return creditsCache.get(id)!;

  const res = await fetch(apiUrl(`/movie/${id}/credits`, { language: 'en-US' }));
  const data: TMDBCredits = await res.json();

  const director = data.crew.find(c => c.job === 'Director')?.name || 'Unknown';
  const cast = data.cast
    .sort((a, b) => a.order - b.order)
    .slice(0, 5)
    .map(c => c.name);

  const result = { director, cast };
  creditsCache.set(id, result);
  return result;
}

export async function fetchFullMovieInfo(id: number): Promise<Partial<Movie>> {
  const [details, credits] = await Promise.all([
    fetchMovieDetails(id),
    fetchMovieCredits(id),
  ]);

  return {
    tagline: details.tagline,
    runtime: details.runtime,
    genres: details.genres,
    genre: details.genres.map(g => g.name).join(', '),
    director: credits.director,
    cast: credits.cast,
  };
}
