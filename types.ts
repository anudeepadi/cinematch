import React from 'react';

export interface Genre {
  id: number;
  name: string;
}

export interface Movie {
  id: string;
  title: string;
  year: number;
  genre: string;
  genres: Genre[];
  description: string;
  rating: number;
  language: string;
  poster_path: string;
  backdrop_path?: string;
  tagline?: string;
  runtime?: number;
  director?: string;
  cast?: string[];
  release_date?: string;
}

export interface SearchState {
  isLoading: boolean;
  query: string;
  recommendations: string[];
  error: string | null;
}

// TMDB API response types

export interface TMDBMovieRaw {
  id: number;
  title: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  release_date: string;
  vote_average: number;
  original_language: string;
  genre_ids: number[];
}

export interface TMDBMovieDetail {
  id: number;
  title: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  release_date: string;
  vote_average: number;
  original_language: string;
  genres: Genre[];
  tagline: string;
  runtime: number;
}

export interface TMDBCredits {
  id: number;
  cast: Array<{
    id: number;
    name: string;
    character: string;
    order: number;
  }>;
  crew: Array<{
    id: number;
    name: string;
    job: string;
    department: string;
  }>;
}

export interface TMDBMovieListResponse {
  page: number;
  results: TMDBMovieRaw[];
  total_pages: number;
  total_results: number;
}

// Add global JSX augmentation for React Three Fiber elements
// We augment both global JSX and React.JSX to cover different TS/React versions.
declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      mesh: any;
      planeGeometry: any;
      boxGeometry: any;
      meshStandardMaterial: any;
      meshBasicMaterial: any;
      color: any;
      ambientLight: any;
      spotLight: any;
      pointLight: any;
      fog: any;
      primitive: any;
    }
  }
}

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      mesh: any;
      planeGeometry: any;
      boxGeometry: any;
      meshStandardMaterial: any;
      meshBasicMaterial: any;
      color: any;
      ambientLight: any;
      spotLight: any;
      pointLight: any;
      fog: any;
      primitive: any;
    }
  }
}
