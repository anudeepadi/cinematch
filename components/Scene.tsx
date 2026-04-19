import React, { useRef, useState, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { MoviePoster } from './MoviePoster';
import { Movie } from '../types';
import { CYLINDER_CONFIG } from '../constants';

interface SceneProps {
  movies: Movie[];
  recommendedIds: string[];
  selectedId?: string;
  onMovieSelect: (id: string) => void;
}

interface CylinderWallProps {
  movies: Movie[];
  recommendedIds: string[];
  selectedId?: string;
  onMovieSelect: (id: string) => void;
}

const { POSTER_WIDTH, POSTER_HEIGHT, GAP, COLUMNS, MIN_MOVIES } = CYLINDER_CONFIG;

// Simple placeholder while poster texture loads
const PosterFallback: React.FC<{ angle: number; y: number; radius: number }> = ({ angle, y, radius }) => {
  const x = Math.sin(angle) * radius;
  const z = Math.cos(angle) * radius;
  return (
    <group position={[x, y, z]} rotation={[0, angle, 0]}>
      <mesh>
        <planeGeometry args={[POSTER_WIDTH, POSTER_HEIGHT]} />
        <meshBasicMaterial color="#111" />
      </mesh>
    </group>
  );
};

const CylinderWall: React.FC<CylinderWallProps> = ({ movies, recommendedIds, selectedId, onMovieSelect }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [targetRotation, setTargetRotation] = useState(0);

  // Tile movies to fill the cylinder if we don't have enough
  const displayMovies = useMemo(() => {
    if (movies.length === 0) return [];
    const timesToTile = Math.max(1, Math.ceil(MIN_MOVIES / movies.length));
    const tiled: (Movie & { uniqueKey: string })[] = [];
    for (let t = 0; t < timesToTile; t++) {
      for (let i = 0; i < movies.length; i++) {
        tiled.push({ ...movies[i], uniqueKey: `${movies[i].id}-${t}-${i}` });
      }
    }
    return tiled;
  }, [movies]);

  const ROWS = Math.ceil(displayMovies.length / COLUMNS);
  const RADIUS = (COLUMNS * (POSTER_WIDTH + GAP)) / (2 * Math.PI);

  // Rotate to selected/recommended movie
  const prevSelectedRef = useRef<string | undefined>(undefined);

  if (selectedId !== prevSelectedRef.current) {
    prevSelectedRef.current = selectedId;
    const targetId = selectedId || (recommendedIds.length > 0 ? recommendedIds[0] : null);

    if (targetId && displayMovies.length > 0) {
      const indices = displayMovies.map((m, i) => m.id === targetId ? i : -1).filter(i => i !== -1);

      if (indices.length > 0) {
        const currentRot = groupRef.current ? groupRef.current.rotation.y : 0;
        let bestDiff = Infinity;
        let bestTargetAngle = 0;

        indices.forEach(index => {
          const colIndex = index % COLUMNS;
          const anglePerCol = (Math.PI * 2) / COLUMNS;
          const movieAngle = colIndex * anglePerCol;
          const targetForThisInstance = -movieAngle;

          let diff = targetForThisInstance - currentRot;
          while (diff > Math.PI) diff -= Math.PI * 2;
          while (diff < -Math.PI) diff += Math.PI * 2;

          if (Math.abs(diff) < Math.abs(bestDiff)) {
            bestDiff = diff;
            bestTargetAngle = currentRot + diff;
          }
        });

        setTargetRotation(bestTargetAngle);
      }
    }
  }

  useFrame((state, delta) => {
    if (groupRef.current) {
      const damp = 3 * delta;
      groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, targetRotation, damp);

      if (!selectedId && recommendedIds.length === 0) {
        groupRef.current.rotation.y += delta * 0.05;
        setTargetRotation(groupRef.current.rotation.y);
      }
    }
  });

  if (displayMovies.length === 0) return null;

  return (
    <group ref={groupRef}>
      {displayMovies.map((movie, index) => {
        const row = Math.floor(index / COLUMNS);
        const col = index % COLUMNS;

        const angle = (col / COLUMNS) * Math.PI * 2;
        const y = (row - (ROWS - 1) / 2) * (POSTER_HEIGHT + GAP);

        const isRecommended = recommendedIds.includes(movie.id);
        const isSelected = selectedId === movie.id;
        const isDimmed = (recommendedIds.length > 0 && !isRecommended);

        return (
          <Suspense
            key={movie.uniqueKey}
            fallback={<PosterFallback angle={angle} y={-y} radius={RADIUS} />}
          >
            <MoviePoster
              movie={movie}
              pos={[angle, -y, RADIUS]}
              isRecommended={isRecommended}
              isDimmed={isDimmed}
              isSelected={isSelected}
              onClick={onMovieSelect}
            />
          </Suspense>
        );
      })}
    </group>
  );
};

export const Scene: React.FC<SceneProps> = ({ movies, recommendedIds, selectedId, onMovieSelect }) => {
  return (
    <Canvas camera={{ position: [0, 0, 38], fov: 45 }}>
      <color attach="background" args={['#050505']} />

      <ambientLight intensity={0.6} />

      <spotLight
        position={[0, 20, 40]}
        angle={0.3}
        penumbra={1}
        intensity={500}
        color="#ffffff"
        distance={100}
      />

      <pointLight position={[30, 0, 20]} intensity={80} color="#6b4cff" distance={60} />
      <pointLight position={[-30, 0, 20]} intensity={80} color="#ff4c8b" distance={60} />

      <CylinderWall
        movies={movies}
        recommendedIds={recommendedIds}
        selectedId={selectedId}
        onMovieSelect={onMovieSelect}
      />

      <fog attach="fog" args={['#050505', 30, 65]} />

      <OrbitControls
        enablePan={false}
        enableZoom={true}
        enableDamping={true}
        dampingFactor={0.05}
        minDistance={20}
        maxDistance={50}
        minPolarAngle={Math.PI / 2 - 0.2}
        maxPolarAngle={Math.PI / 2 + 0.2}
        rotateSpeed={0.4}
      />
    </Canvas>
  );
};
