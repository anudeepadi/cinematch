import React, { useRef, useState, useEffect } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';
import { Movie } from '../types';
import { getPosterUrl } from '../services/tmdbService';

interface MoviePosterProps {
  movie: Movie;
  pos: [number, number, number];
  isRecommended: boolean;
  isDimmed: boolean;
  isSelected: boolean;
  onClick: (id: string) => void;
}

const WIDTH = 3;
const HEIGHT = 4.5;
const BORDER_THICKNESS = 0.06;

export const MoviePoster: React.FC<MoviePosterProps> = ({
  movie,
  pos,
  isRecommended,
  isDimmed,
  isSelected,
  onClick
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  const [angle, y, radius] = pos;

  const x = Math.sin(angle) * radius;
  const z = Math.cos(angle) * radius;

  const imageUrl = getPosterUrl(movie.poster_path, 'w342');

  // Use R3F's useLoader which integrates with Suspense
  const texture = useLoader(THREE.TextureLoader, imageUrl);

  const randomOffset = useRef(Math.random() * 100);

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = angle;

      const targetScale = hovered ? 1.05 : (isSelected ? 1.03 : 1);
      groupRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), delta * 8);

      if (isSelected || isRecommended) {
        const time = state.clock.elapsedTime + randomOffset.current;
        const floatY = Math.sin(time * 2) * 0.08;
        groupRef.current.position.y = y + floatY;
      } else {
        groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, y, delta * 4);
      }
    }
  });

  const showBorder = isSelected || hovered;
  const dimmed = isDimmed && !hovered && !isSelected;

  return (
    <group
      ref={groupRef}
      position={[x, y, z]}
    >
      {/* Hit box */}
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          onClick(movie.id);
        }}
        onPointerOver={() => { document.body.style.cursor = 'pointer'; setHovered(true); }}
        onPointerOut={() => { document.body.style.cursor = 'auto'; setHovered(false); }}
      >
        <boxGeometry args={[WIDTH, HEIGHT, 1]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>

      {/* White border — 4 thin planes forming a rectangle */}
      {showBorder && (
        <>
          {/* Top */}
          <mesh position={[0, HEIGHT / 2, -0.01]}>
            <planeGeometry args={[WIDTH + BORDER_THICKNESS * 2, BORDER_THICKNESS]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={isSelected ? 0.9 : 0.5} />
          </mesh>
          {/* Bottom */}
          <mesh position={[0, -HEIGHT / 2, -0.01]}>
            <planeGeometry args={[WIDTH + BORDER_THICKNESS * 2, BORDER_THICKNESS]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={isSelected ? 0.9 : 0.5} />
          </mesh>
          {/* Left */}
          <mesh position={[-WIDTH / 2, 0, -0.01]}>
            <planeGeometry args={[BORDER_THICKNESS, HEIGHT]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={isSelected ? 0.9 : 0.5} />
          </mesh>
          {/* Right */}
          <mesh position={[WIDTH / 2, 0, -0.01]}>
            <planeGeometry args={[BORDER_THICKNESS, HEIGHT]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={isSelected ? 0.9 : 0.5} />
          </mesh>
        </>
      )}

      {/* Backing Mesh */}
      <mesh position={[0, 0, -0.02]} raycast={() => null}>
        <planeGeometry args={[WIDTH, HEIGHT]} />
        <meshStandardMaterial
          color="#050505"
          metalness={0.9}
          roughness={0.1}
        />
      </mesh>

      {/* Poster Image - using manual texture mesh */}
      <mesh raycast={() => null}>
        <planeGeometry args={[WIDTH, HEIGHT]} />
        <meshBasicMaterial
          map={texture}
          transparent
          opacity={dimmed ? 0.2 : 1}
          color={dimmed ? '#333333' : '#ffffff'}
          toneMapped={false}
        />
      </mesh>

      {/* Title */}
      {(hovered || isSelected) && (
        <Text
          position={[0, -HEIGHT / 2 - 0.3, 0.1]}
          fontSize={0.25}
          color={isSelected ? "#ddd" : "white"}
          anchorX="center"
          anchorY="top"
          maxWidth={3.2}
          raycast={() => null}
        >
          {movie.title}
        </Text>
      )}
    </group>
  );
};
