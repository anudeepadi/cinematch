import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, MeshReflectorMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { MoviePoster } from './MoviePoster';
import { MOVIE_DB } from '../constants';

interface SceneProps {
  recommendedIds: string[];
  selectedId?: string;
  onMovieSelect: (id: string) => void;
}

const CylinderWall: React.FC<SceneProps> = ({ recommendedIds, selectedId, onMovieSelect }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [targetRotation, setTargetRotation] = useState(0);

  // Configuration for Dense Wall
  const POSTER_WIDTH = 3;
  const POSTER_HEIGHT = 4.8;
  const GAP = 0.05; 
  
  // Create a larger dataset to fill the wall
  const displayMovies = useMemo(() => {
    // Tile the database multiple times
    return [...MOVIE_DB, ...MOVIE_DB, ...MOVIE_DB, ...MOVIE_DB, ...MOVIE_DB].map((m, i) => ({
      ...m,
      uniqueKey: `${m.id}-${i}`
    }));
  }, []);

  const COLUMNS = 20; 
  const ROWS = Math.ceil(displayMovies.length / COLUMNS);
  
  // Radius calculation
  const RADIUS = (COLUMNS * (POSTER_WIDTH + GAP)) / (2 * Math.PI);

  useEffect(() => {
    // Determine target movie to center
    const targetId = selectedId || (recommendedIds.length > 0 ? recommendedIds[0] : null);

    if (targetId) {
      // Find all instances of this movie
      const indices = displayMovies.map((m, i) => m.id === targetId ? i : -1).filter(i => i !== -1);
      
      if (indices.length > 0) {
        // Calculate angles for all instances to find the one requiring minimal rotation
        const currentRot = groupRef.current ? groupRef.current.rotation.y : 0;
        
        let bestDiff = Infinity;
        let bestTargetAngle = 0;

        indices.forEach(index => {
          const colIndex = index % COLUMNS;
          const anglePerCol = (Math.PI * 2) / COLUMNS;
          const movieAngle = colIndex * anglePerCol;
          const targetForThisInstance = -movieAngle;

          // Normalize diff to find shortest path
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
  }, [selectedId, recommendedIds, COLUMNS, displayMovies]);

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Smooth interpolation for selection rotation
      const damp = 3 * delta;
      groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, targetRotation, damp);
      
      // Auto-rotate if no active selection and no recommendations
      if (!selectedId && recommendedIds.length === 0) {
         groupRef.current.rotation.y += delta * 0.05;
         setTargetRotation(groupRef.current.rotation.y);
      }
    }
  });

  return (
    <group ref={groupRef}>
      {displayMovies.map((movie, index) => {
        const row = Math.floor(index / COLUMNS);
        const col = index % COLUMNS;
        
        const angle = (col / COLUMNS) * Math.PI * 2;
        // Center the rows vertically
        const y = (row - (ROWS - 1) / 2) * (POSTER_HEIGHT + GAP);
        
        const isRecommended = recommendedIds.includes(movie.id);
        const isSelected = selectedId === movie.id;
        
        // Dimming logic: Dim everything if there are recommendations, except the recommended ones.
        // If nothing is recommended, nothing is dimmed.
        const isDimmed = (recommendedIds.length > 0 && !isRecommended);

        return (
          <MoviePoster
            key={movie.uniqueKey}
            movie={movie}
            pos={[angle, -y, RADIUS]}
            isRecommended={isRecommended}
            isDimmed={isDimmed}
            isSelected={isSelected}
            onClick={onMovieSelect}
          />
        );
      })}
    </group>
  );
};

export const Scene: React.FC<SceneProps> = ({ recommendedIds, selectedId, onMovieSelect }) => {
  return (
    <Canvas camera={{ position: [0, 0, 38], fov: 45 }}>
      <color attach="background" args={['#050505']} />
      
      {/* Cinematic Lighting */}
      <ambientLight intensity={0.2} />
      
      <spotLight 
        position={[0, 20, 40]} 
        angle={0.25} 
        penumbra={1} 
        intensity={800} 
        color="#ffffff" 
        distance={100}
        castShadow
      />

      <pointLight position={[30, 0, 20]} intensity={100} color="#6b4cff" distance={60} />
      <pointLight position={[-30, 0, 20]} intensity={100} color="#ff4c8b" distance={60} />

      <CylinderWall recommendedIds={recommendedIds} selectedId={selectedId} onMovieSelect={onMovieSelect} />
      
      {/* Reflective Floor - Lowered to accommodate full cylinder height */}
      <mesh position={[0, -22, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[100, 100]} />
        <MeshReflectorMaterial
          blur={[300, 100]}
          resolution={1024}
          mixBlur={1}
          mixStrength={40}
          roughness={1}
          depthScale={1.2}
          minDepthThreshold={0.4}
          maxDepthThreshold={1.4}
          color="#0a0a0a"
          metalness={0.5}
          mirror={0.75}
        />
      </mesh>

      <Environment preset="city" />
      <fog attach="fog" args={['#050505', 25, 60]} />
      
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
