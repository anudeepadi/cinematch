import React from 'react';

export interface Movie {
  id: string;
  title: string;
  year: number;
  genre: string;
  description: string;
  rating: number;
  language: string;
}

export interface SearchState {
  isLoading: boolean;
  query: string;
  recommendations: string[]; // List of movie IDs
  error: string | null;
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