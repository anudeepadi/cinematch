import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Image, Text } from '@react-three/drei';
import * as THREE from 'three';
import { Movie } from '../types';

interface MoviePosterProps {
  movie: Movie;
  pos: [number, number, number]; // [angle, y, radius]
  isRecommended: boolean;
  isDimmed: boolean;
  isSelected: boolean;
  onClick: (id: string) => void;
}

// Updated dimensions from Scene.tsx (3 x 4.8)
const WIDTH = 3;
const HEIGHT = 4.8;

export const MoviePoster: React.FC<MoviePosterProps> = ({ 
  movie, 
  pos, 
  isRecommended, 
  isDimmed,
  isSelected,
  onClick 
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const [angle, y, radius] = pos;

  const x = Math.sin(angle) * radius;
  const z = Math.cos(angle) * radius;

  const imageUrl = `https://picsum.photos/400/640?random=${movie.id}`;

  // Random offset for floating animation to desynchronize them
  const randomOffset = useRef(Math.random() * 100);

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Base rotation: Face outwards
      groupRef.current.rotation.y = angle;

      // Scale effect: Hover scales up. Selected also scales up slightly if not hovered.
      const targetScale = hovered ? 1.1 : (isSelected ? 1.05 : 1);
      groupRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), delta * 8);

      // Floating animation for selected or recommended items
      if (isSelected || isRecommended) {
        const time = state.clock.elapsedTime + randomOffset.current;
        // Float on Y axis
        const floatY = Math.sin(time * 2) * 0.1;
        groupRef.current.position.y = y + floatY;
      } else {
        groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, y, delta * 4);
      }
    }
    
    // Pulse the glow for selected item
    if (glowRef.current && isSelected) {
       glowRef.current.material.opacity = 0.5 + Math.sin(state.clock.elapsedTime * 3) * 0.2;
    }
  });

  return (
    <group 
      ref={groupRef} 
      position={[x, y, z]}
    >
      {/* 
        HIT BOX: Volumetric transparent box
      */}
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

      {/* Selected Glow Border (Behind) */}
      {(isSelected || hovered) && (
        <mesh position={[0, 0, -0.05]} ref={glowRef}>
          <planeGeometry args={[WIDTH + 0.2, HEIGHT + 0.2]} />
          <meshBasicMaterial color={isSelected ? "#8b5cf6" : "#ffffff"} transparent opacity={0.5} />
        </mesh>
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

      {/* Poster Image */}
      <Image 
        url={imageUrl}
        transparent
        opacity={isDimmed && !hovered && !isSelected ? 0.2 : 1}
        color={isDimmed && !hovered && !isSelected ? "#333" : "white"} 
        scale={[WIDTH, HEIGHT, 1]}
        raycast={() => null} 
      />
      
      {/* Title */}
      {(hovered || isSelected) && (
        <Text
          position={[0, -HEIGHT/2 - 0.3, 0.1]} // Move text below poster for cleaner look
          fontSize={0.25} 
          color={isSelected ? "#ddd" : "white"}
          anchorX="center"
          anchorY="top"
          maxWidth={3.2}
          font="https://fonts.gstatic.com/s/playfairdisplay/v30/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKdFvXDXbtM.woff"
          raycast={() => null}
        >
          {movie.title}
        </Text>
      )}
    </group>
  );
};
